"""Verit Image AI — Strong detector.

A single modern ViT classifier (`dima806/ai_vs_real_image_detection`)
exposed on the same HTTP contract as the DeepSafe-SDK image services so
the orchestrator can ensemble it with NPR and UF transparently.

To swap in a different HuggingFace classifier later, change MODEL_ID
below and rebuild — the label resolver auto-detects which class index
corresponds to "AI"/"fake"/"synthetic" so most binary classifiers will
work without code changes.
"""
import base64
import io
import os
import time
from contextlib import asynccontextmanager

import torch
from PIL import Image
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoImageProcessor, AutoModelForImageClassification

MODEL_ID = os.environ.get("MODEL_ID", "dima806/ai_vs_real_image_detection")
FAKE_TOKENS = (
    "fake", "ai", "artificial", "synthetic", "generated",
    "deepfake", "manipulated", "gan",
)

device = torch.device("cpu")
state = {"processor": None, "model": None, "fake_idx": None}


def _resolve_fake_idx(id2label: dict) -> int:
    """Find which class index corresponds to the AI/fake label."""
    for k, v in id2label.items():
        if any(t in str(v).lower() for t in FAKE_TOKENS):
            return int(k)
    # Fallback: assume index 0 is fake (will be wrong for some models;
    # MODEL_ID env override lets you fix it without code changes).
    return 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Loading model: {MODEL_ID}")
    proc = AutoImageProcessor.from_pretrained(MODEL_ID)
    net = AutoModelForImageClassification.from_pretrained(MODEL_ID).to(device).eval()
    fake_idx = _resolve_fake_idx({int(k): v for k, v in net.config.id2label.items()})
    state["processor"] = proc
    state["model"] = net
    state["fake_idx"] = fake_idx
    print(f"Model ready. id2label={dict(net.config.id2label)}, fake_idx={fake_idx}")
    yield
    state.clear()


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
        "model_id": MODEL_ID,
        "model_loaded": state.get("model") is not None,
    }


@app.post("/predict")
def predict(req: PredictRequest):
    t0 = time.time()
    if state.get("model") is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")
    try:
        raw = base64.b64decode(req.image_data)
        img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot decode image: {e}")

    inputs = state["processor"](images=img, return_tensors="pt").to(device)
    with torch.no_grad():
        logits = state["model"](**inputs).logits
        probs = torch.softmax(logits, dim=-1)
    score = float(probs[0, state["fake_idx"]].item())

    return {
        "probability": score,
        "prediction": 1 if score >= req.threshold else 0,
        "class": "fake" if score >= req.threshold else "real",
        "model": MODEL_ID,
        "inference_time": round(time.time() - t0, 3),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
