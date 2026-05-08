"""Verit Image AI — Strong detector (2-model ensemble).

Runs two complementary HuggingFace classifiers and averages their
probabilities of "AI". Different architectures (Swin + SigLIP) trained on
different data give us robustness to single-model failure modes (most
notably the over-prediction problem that plagued the previous single-
model setup).

Per-model weights are env-overridable, so if one model misbehaves on your
inputs you can set its weight to 0 without changing code.
"""
import base64
import io
import os
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Tuple

import torch
from PIL import Image
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoImageProcessor, AutoModelForImageClassification

# (model_id, default_weight). Override per-model weight via env vars.
DEFAULT_MODELS: List[Tuple[str, float]] = [
    ("Organika/sdxl-detector", 0.50),
    ("Ateeqq/ai-vs-human-image-detector", 0.50),
]

FAKE_TOKENS = (
    "fake", "ai", "artificial", "synthetic", "generated",
    "deepfake", "manipulated", "gan",
)
REAL_TOKENS = ("real", "human", "natural", "authentic", "genuine", "photo")


def _resolve_fake_idx(id2label: Dict[int, str]) -> int:
    """Pick the class index whose label semantically means 'AI/fake'.

    Uses word-boundary aware matching to avoid false hits like 'main' for
    'ai'. If both labels are ambiguous, prefer the one that matches a
    fake-token over one that matches a real-token.
    """
    fake_hits: List[int] = []
    real_hits: List[int] = []
    for k, v in id2label.items():
        s = str(v).lower().strip()
        # word-boundary check for short tokens
        words = set(s.replace("-", " ").replace("_", " ").split())
        if any(t in words for t in FAKE_TOKENS) or any(t in s for t in ("artificial", "synthetic", "generated", "deepfake")):
            fake_hits.append(int(k))
        if any(t in words for t in REAL_TOKENS) or any(t in s for t in ("human", "authentic")):
            real_hits.append(int(k))
    if fake_hits:
        return fake_hits[0]
    # No explicit fake label found — fall back to "the index that is NOT
    # the real label" if we have a real hit.
    if real_hits:
        for idx in id2label:
            if int(idx) not in real_hits:
                return int(idx)
    return 0


def _model_weight(model_id: str, default: float) -> float:
    """Per-model weight env override. Slug = ID with non-alnum -> underscore.
    e.g. WEIGHT_ORGANIKA_SDXL_DETECTOR=0.7
    """
    slug = "WEIGHT_" + "".join(
        c.upper() if c.isalnum() else "_" for c in model_id
    ).strip("_")
    raw = os.environ.get(slug)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


loaded: List[dict] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading strong-ensemble models...")
    for model_id, default_weight in DEFAULT_MODELS:
        weight = _model_weight(model_id, default_weight)
        if weight <= 0:
            print(f"  skip {model_id} (weight={weight})")
            continue
        proc = AutoImageProcessor.from_pretrained(model_id)
        net = AutoModelForImageClassification.from_pretrained(model_id).eval()
        id2label = {int(k): v for k, v in net.config.id2label.items()}
        fake_idx = _resolve_fake_idx(id2label)
        loaded.append({
            "id": model_id,
            "processor": proc,
            "model": net,
            "fake_idx": fake_idx,
            "weight": weight,
            "id2label": id2label,
        })
        print(f"  loaded {model_id}  id2label={id2label}  fake_idx={fake_idx}  weight={weight}")
    if not loaded:
        print("WARNING: no models loaded (all weights <= 0)")
    print(f"Strong ensemble ready ({len(loaded)} models).")
    yield
    loaded.clear()


app = FastAPI(title="Verit Image Strong Detector", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


class PredictRequest(BaseModel):
    image_data: str          # base64-encoded image bytes
    threshold: float = 0.5


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "models": [m["id"] for m in loaded],
        "model_loaded": len(loaded) > 0,
    }


@app.post("/predict")
def predict(req: PredictRequest):
    t0 = time.time()
    if not loaded:
        raise HTTPException(status_code=503, detail="No models loaded")
    try:
        raw = base64.b64decode(req.image_data)
        img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot decode image: {e}")

    components = []
    weighted_sum = 0.0
    total_weight = 0.0
    for m in loaded:
        try:
            inputs = m["processor"](images=img, return_tensors="pt")
            with torch.no_grad():
                logits = m["model"](**inputs).logits
                probs = torch.softmax(logits, dim=-1)
            score = float(probs[0, m["fake_idx"]].item())
        except Exception as e:
            print(f"  inference error on {m['id']}: {e}")
            continue
        components.append({
            "model": m["id"],
            "probability": round(score, 4),
            "weight": m["weight"],
        })
        weighted_sum += score * m["weight"]
        total_weight += m["weight"]

    if total_weight == 0:
        raise HTTPException(status_code=500, detail="All in-Space models failed inference")

    probability = weighted_sum / total_weight

    return {
        "probability": probability,
        "prediction": 1 if probability >= req.threshold else 0,
        "class": "fake" if probability >= req.threshold else "real",
        "model": "ensemble[" + ",".join(c["model"].split("/")[-1] for c in components) + "]",
        "inference_time": round(time.time() - t0, 3),
        "components": components,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
