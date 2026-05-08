import base64
import os
from typing import Optional

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

DEEPSAFE_URL = os.getenv("DEEPSAFE_URL", "http://localhost:5001").rstrip("/")
# DEEPSAFE_MODE: "single_model" -> POST /predict with base64 JSON (a single DeepSafe model service)
#                "orchestrator" -> POST /detect with multipart file (the full DeepSafe API on port 8000)
DEEPSAFE_MODE = os.getenv("DEEPSAFE_MODE", "single_model").lower()
VIDEO_URL = os.getenv("VIDEO_URL", "http://localhost:5005").rstrip("/")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "600"))

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".tif"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v"}

app = FastAPI(title="AI Detection Orchestrator", version="1.0.0")

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


def normalize_image_response(data: dict) -> dict:
    # Two response shapes supported:
    #  - Orchestrator /detect: { is_likely_deepfake, deepfake_probability, ... }
    #  - Single model /predict: { probability, prediction, class, model, inference_time }
    if "is_likely_deepfake" in data:
        is_fake = bool(data.get("is_likely_deepfake"))
        ai_prob = float(data.get("deepfake_probability", 0.5))
        details = {
            "model_count": data.get("model_count"),
            "fake_votes": data.get("fake_votes"),
            "real_votes": data.get("real_votes"),
            "response_time": data.get("response_time"),
        }
    else:
        ai_prob = float(data.get("probability", 0.5))
        is_fake = int(data.get("prediction", 0)) == 1
        details = {
            "model": data.get("model"),
            "inference_time": data.get("inference_time"),
        }
    return {
        "type": "image",
        "verdict": "AI" if is_fake else "Real",
        "ai_probability": ai_prob,
        "confidence": ai_prob if is_fake else 1.0 - ai_prob,
        "service": "deepsafe",
        "details": details,
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
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in (("deepsafe", DEEPSAFE_URL), ("video", VIDEO_URL)):
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
        target_url = DEEPSAFE_URL
        if DEEPSAFE_MODE == "single_model":
            target_path = "/predict"
            request_kwargs = {
                "json": {
                    "image_data": base64.b64encode(payload).decode("ascii"),
                    "threshold": 0.5,
                },
            }
        else:
            target_path = "/detect"
            request_kwargs = {
                "files": {
                    "file": (
                        file.filename or "upload",
                        payload,
                        file.content_type or "application/octet-stream",
                    )
                },
            }
    else:
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
            detail=f"{media_type.capitalize()} detection service is unreachable at {target_url}.",
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"{media_type.capitalize()} detection service timed out after {REQUEST_TIMEOUT}s.",
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Network error contacting {media_type} service: {type(e).__name__}",
        )

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text[:300])
        except ValueError:
            detail = response.text[:300] or f"HTTP {response.status_code}"
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{media_type.capitalize()} service error: {detail}",
        )

    try:
        data = response.json()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{media_type.capitalize()} service returned non-JSON response.",
        )

    if media_type == "image":
        return normalize_image_response(data)
    return normalize_video_response(data)
