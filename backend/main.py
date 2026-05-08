import asyncio
import base64
import logging
import os
from typing import List, Optional, Tuple

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from metadata_check import MetadataFinding, check as metadata_check

logger = logging.getLogger("orchestrator")

DEEPSAFE_URL = os.getenv("DEEPSAFE_URL", "http://localhost:5001").rstrip("/")
# Optional second image service (UniversalFakeDetect — CLIP ViT-L/14).
DEEPSAFE_URL_UF = os.getenv("DEEPSAFE_URL_UF", "").rstrip("/")
# Optional third image service (a strong modern ViT classifier such as
# dima806/ai_vs_real_image_detection). When set, all image requests go
# to NPR + UF + Strong in parallel and the probabilities are combined.
DEEPSAFE_URL_STRONG = os.getenv("DEEPSAFE_URL_STRONG", "").rstrip("/")
# DEEPSAFE_MODE: "single_model" -> POST /predict with base64 JSON (a single DeepSafe model service)
#                "orchestrator" -> POST /detect with multipart file (the full DeepSafe API on port 8000)
DEEPSAFE_MODE = os.getenv("DEEPSAFE_MODE", "single_model").lower()
VIDEO_URL = os.getenv("VIDEO_URL", "http://localhost:5005").rstrip("/")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "600"))

# ── Ensemble tuning (all env-var configurable) ──────────────────────────
# Defaults assume all three services are available. NPR is the weakest on
# modern diffusion (it's GAN-era) so it gets the smallest weight; UF
# (CLIP-based) is moderately strong; Strong (modern ViT classifier) is the
# main signal. Weights are normalized at runtime to sum to 1, so dropping
# a service just rescales the others — no need to retune when toggling.
W_NPR = float(os.getenv("ENSEMBLE_WEIGHT_NPR", "0.15"))
W_UF = float(os.getenv("ENSEMBLE_WEIGHT_UF", "0.35"))
W_STRONG = float(os.getenv("ENSEMBLE_WEIGHT_STRONG", "0.50"))
# Decision threshold on the weighted probability. Lower than 0.5 because
# CPU-only detectors trained on older data tend to under-predict on modern
# AI generators — we accept some false-positive risk to reduce FN.
AI_THRESHOLD = float(os.getenv("AI_THRESHOLD", "0.40"))
# Aggressive trip-wire: if ANY single model exceeds this score on its own,
# flag as AI even if the weighted average doesn't cross AI_THRESHOLD. Set
# to 1.01 to disable.
AGGRESSIVE_MAX = float(os.getenv("ENSEMBLE_AGGRESSIVE_MAX", "0.55"))
# Probability we report when only metadata fires (not from any model).
METADATA_PROB = float(os.getenv("METADATA_PROB", "0.95"))

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".tif"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v"}

app = FastAPI(title="AI Detection Orchestrator", version="1.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def detect_media_type(file: UploadFile) -> Optional[str]:
    if file.content_type:
        if file.content_type.startswith("image/"):
            return "image"
        if file.content_type.startswith("video/"):
            return "video"
    if file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext in IMAGE_EXTS:
            return "image"
        if ext in VIDEO_EXTS:
            return "video"
    return None


def _safe_metadata_check(raw: bytes) -> Optional[MetadataFinding]:
    try:
        return metadata_check(raw)
    except Exception as e:
        logger.warning("metadata_check raised %s; ignoring", type(e).__name__)
        return None


def metadata_short_circuit(finding: MetadataFinding) -> dict:
    # Cap reported probability at METADATA_PROB regardless of finding's own
    # value, so behaviour is uniform and operator-tunable.
    prob = max(finding.probability, METADATA_PROB)
    return {
        "type": "image",
        "verdict": "AI",
        "ai_probability": round(prob, 4),
        "confidence": round(prob, 4),
        "service": "metadata",
        "details": {
            "metadata_source": finding.source,
            "field": finding.field,
            "evidence": finding.evidence,
            "note": "Detected an AI-generation tell in the file's metadata. "
                    "This is a strong positive signal but can be evaded by "
                    "stripping metadata.",
        },
    }


async def _call_single_model(
    client: httpx.AsyncClient, base_url: str, image_b64: str
) -> Tuple[Optional[dict], Optional[str]]:
    """Returns (json_response, None) on success or (None, error_message)."""
    try:
        r = await client.post(
            f"{base_url}/predict",
            json={"image_data": image_b64, "threshold": 0.5},
        )
    except httpx.ConnectError:
        return None, f"unreachable ({base_url})"
    except httpx.TimeoutException:
        return None, f"timeout ({base_url})"
    except httpx.HTTPError as e:
        return None, f"{type(e).__name__} ({base_url})"

    if r.status_code >= 400:
        try:
            detail = r.json().get("detail", r.text[:200])
        except ValueError:
            detail = r.text[:200] or f"HTTP {r.status_code}"
        return None, f"upstream {r.status_code}: {detail}"
    try:
        return r.json(), None
    except ValueError:
        return None, "non-JSON response"


def normalize_image_response_orchestrator(data: dict) -> dict:
    """For the full DeepSafe orchestrator path (DEEPSAFE_MODE=orchestrator)."""
    is_fake = bool(data.get("is_likely_deepfake"))
    ai_prob = float(data.get("deepfake_probability", 0.5))
    return {
        "type": "image",
        "verdict": "AI" if is_fake else "Real",
        "ai_probability": ai_prob,
        "confidence": ai_prob if is_fake else 1.0 - ai_prob,
        "service": "deepsafe",
        "details": {
            "model_count": data.get("model_count"),
            "fake_votes": data.get("fake_votes"),
            "real_votes": data.get("real_votes"),
            "response_time": data.get("response_time"),
        },
    }


def _model_weight(label: str) -> float:
    if label == "npr":
        return W_NPR
    if label == "uf":
        return W_UF
    if label == "strong":
        return W_STRONG
    return 1.0


def normalize_ensemble(model_results: List[Tuple[str, dict]]) -> dict:
    """model_results = [(label, json_response), ...] in the order called.

    Decision rule (all configurable via env vars):
      1. weighted_avg = sum(weight * prob) / sum(weight)
      2. is_fake if weighted_avg >= AI_THRESHOLD
                 OR max(individual_probs) >= AGGRESSIVE_MAX
    """
    probs = [(label, float(r.get("probability", 0.5))) for label, r in model_results]
    weights = [_model_weight(label) for label, _ in probs]
    weighted_sum = sum(w * p for w, (_, p) in zip(weights, probs))
    total_w = sum(weights) or 1.0
    weighted_avg = weighted_sum / total_w
    max_prob = max(p for _, p in probs)

    threshold_trip = weighted_avg >= AI_THRESHOLD
    max_trip = max_prob >= AGGRESSIVE_MAX
    is_fake = threshold_trip or max_trip

    # Reported ai_probability is the higher of (weighted_avg, max_prob)
    # — so a single confident model isn't drowned out by an unsure peer.
    ai_prob = max(weighted_avg, max_prob if max_trip else 0.0)
    ai_prob = max(0.0, min(1.0, ai_prob))

    components = [
        {
            "model": label,
            "probability": round(p, 4),
            "weight": _model_weight(label),
            "raw_model_id": r.get("model"),
        }
        for (label, p), (_, r) in zip(probs, model_results)
    ]
    service = "ensemble[" + ",".join(label for label, _ in model_results) + "]"
    strategy = "weighted_avg+max"
    if len(model_results) == 1:
        service = "single[" + model_results[0][0] + "]"
        strategy = "single"

    decision_reason = []
    if threshold_trip:
        decision_reason.append(
            f"weighted_avg {weighted_avg:.3f} >= AI_THRESHOLD {AI_THRESHOLD:.2f}"
        )
    if max_trip:
        decision_reason.append(
            f"max_prob {max_prob:.3f} >= AGGRESSIVE_MAX {AGGRESSIVE_MAX:.2f}"
        )
    if not decision_reason:
        decision_reason.append(
            f"weighted_avg {weighted_avg:.3f} < AI_THRESHOLD {AI_THRESHOLD:.2f}"
        )

    return {
        "type": "image",
        "verdict": "AI" if is_fake else "Real",
        "ai_probability": round(ai_prob, 4),
        "confidence": round(ai_prob if is_fake else 1.0 - weighted_avg, 4),
        "service": service,
        "details": {
            "components": components,
            "weighted_avg": round(weighted_avg, 4),
            "max_prob": round(max_prob, 4),
            "thresholds": {
                "ai_threshold": AI_THRESHOLD,
                "aggressive_max": AGGRESSIVE_MAX,
            },
            "strategy": strategy,
            "decision": " AND ".join(decision_reason),
        },
    }


def normalize_video_response(data: dict) -> dict:
    ai_prob = float(data.get("ai_probability", 0.5))
    is_fake = ai_prob >= 0.5
    return {
        "type": "video",
        "verdict": "AI" if is_fake else "Real",
        "ai_probability": ai_prob,
        "confidence": ai_prob if is_fake else 1.0 - ai_prob,
        "service": "video-detector",
        "details": data.get("details", {}),
    }


@app.get("/health")
async def health():
    services = {"orchestrator": "healthy"}
    targets = [("deepsafe", DEEPSAFE_URL), ("video", VIDEO_URL)]
    if DEEPSAFE_URL_UF:
        targets.insert(1, ("deepsafe_uf", DEEPSAFE_URL_UF))
    if DEEPSAFE_URL_STRONG:
        targets.insert(-1, ("deepsafe_strong", DEEPSAFE_URL_STRONG))
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in targets:
            try:
                r = await client.get(f"{url}/health")
                services[name] = "healthy" if r.status_code == 200 else f"unhealthy ({r.status_code})"
            except httpx.HTTPError as e:
                services[name] = f"unreachable ({type(e).__name__})"
    return {"services": services}


@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    media_type = detect_media_type(file)
    if media_type is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Upload an image or video. (got content_type='{file.content_type}', filename='{file.filename}')",
        )

    payload = await file.read()
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if media_type == "image":
        # 1) Metadata short-circuit. Wrapped to never block on parser errors.
        finding = _safe_metadata_check(payload)
        if finding is not None:
            return metadata_short_circuit(finding)

        # 2) DeepSafe orchestrator mode keeps its old single-call path.
        if DEEPSAFE_MODE != "single_model":
            data, err = await _call_orchestrator(payload, file)
            if err:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=err)
            return normalize_image_response_orchestrator(data)

        # 3) single_model mode: call NPR (and UF / Strong if configured) in parallel.
        image_b64 = base64.b64encode(payload).decode("ascii")
        targets: List[Tuple[str, str]] = [("npr", DEEPSAFE_URL)]
        if DEEPSAFE_URL_UF:
            targets.append(("uf", DEEPSAFE_URL_UF))
        if DEEPSAFE_URL_STRONG:
            targets.append(("strong", DEEPSAFE_URL_STRONG))

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            calls = [_call_single_model(client, url, image_b64) for _, url in targets]
            outcomes = await asyncio.gather(*calls)

        successes: List[Tuple[str, dict]] = []
        errors: List[Tuple[str, str]] = []
        for (label, _), (data, err) in zip(targets, outcomes):
            if data is not None:
                successes.append((label, data))
            else:
                errors.append((label, err or "unknown error"))

        if not successes:
            joined = "; ".join(f"{lbl}: {msg}" for lbl, msg in errors)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"All image services failed. {joined}",
            )

        result = normalize_ensemble(successes)
        if errors:
            result["details"]["partial_failure"] = [
                {"model": lbl, "error": msg} for lbl, msg in errors
            ]
        return result

    # Video branch — unchanged.
    target_url = VIDEO_URL
    target_path = "/predict"
    request_kwargs = {
        "files": {
            "file": (
                file.filename or "upload",
                payload,
                file.content_type or "application/octet-stream",
            )
        },
    }
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(f"{target_url}{target_path}", **request_kwargs)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Video detection service is unreachable at {target_url}.",
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Video detection service timed out after {REQUEST_TIMEOUT}s.",
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Network error contacting video service: {type(e).__name__}",
        )

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text[:300])
        except ValueError:
            detail = response.text[:300] or f"HTTP {response.status_code}"
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Video service error: {detail}",
        )

    try:
        data = response.json()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Video service returned non-JSON response.",
        )
    return normalize_video_response(data)


async def _call_orchestrator(
    payload: bytes, file: UploadFile
) -> Tuple[Optional[dict], Optional[str]]:
    request_kwargs = {
        "files": {
            "file": (
                file.filename or "upload",
                payload,
                file.content_type or "application/octet-stream",
            )
        },
    }
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            r = await client.post(f"{DEEPSAFE_URL}/detect", **request_kwargs)
    except httpx.ConnectError:
        return None, f"DeepSafe orchestrator unreachable at {DEEPSAFE_URL}."
    except httpx.TimeoutException:
        return None, f"DeepSafe orchestrator timed out after {REQUEST_TIMEOUT}s."
    except httpx.HTTPError as e:
        return None, f"Network error: {type(e).__name__}"
    if r.status_code >= 400:
        try:
            detail = r.json().get("detail", r.text[:300])
        except ValueError:
            detail = r.text[:300] or f"HTTP {r.status_code}"
        return None, f"DeepSafe error: {detail}"
    try:
        return r.json(), None
    except ValueError:
        return None, "DeepSafe returned non-JSON."
