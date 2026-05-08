import base64
import io
import os
from contextlib import asynccontextmanager
from typing import List, Tuple

import numpy as np
import torch
from PIL import Image
from facenet_pytorch import MTCNN
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoImageProcessor, AutoModelForImageClassification

ENSEMBLE_SPEC: List[Tuple[str, float]] = [
    ("prithivMLmods/Deep-Fake-Detector-Model", 0.6),
    ("prithivMLmods/Deep-Fake-Detector-v2-Model", 0.4),
]
FAKE_TOKENS = ("fake", "deepfake", "manipulated", "synthetic")
FACE_THRESHOLDS = [0.7, 0.8, 0.8]

device = torch.device("cpu")
models = []       # (processor, net, fake_idx, weight)
face_detector = None


def _resolve_fake_idx(id2label: dict) -> int:
    for k, v in id2label.items():
        if any(t in str(v).lower() for t in FAKE_TOKENS):
            return int(k)
    return 0


def _square_crop(arr: np.ndarray, box) -> np.ndarray:
    xmin, ymin, xmax, ymax = [int(b) for b in box]
    w, h = xmax - xmin, ymax - ymin
    pw = (h - w) // 2 if h > w else 0
    ph = (w - h) // 2 if w > h else 0
    x1, y1 = max(0, xmin - pw), max(0, ymin - ph)
    x2, y2 = min(arr.shape[1], xmax + pw), min(arr.shape[0], ymax + ph)
    return arr[y1:y2, x1:x2]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global models, face_detector
    print("Loading models...")
    for name, weight in ENSEMBLE_SPEC:
        proc = AutoImageProcessor.from_pretrained(name)
        net = AutoModelForImageClassification.from_pretrained(name).to(device).eval()
        fake_idx = _resolve_fake_idx({int(k): str(v) for k, v in net.config.id2label.items()})
        models.append((proc, net, fake_idx, weight))
    face_detector = MTCNN(
        keep_all=True, device=device,
        thresholds=FACE_THRESHOLDS, min_face_size=40, select_largest=False,
    )
    print("Models ready.")
    yield
    models.clear()


app = FastAPI(title="Image Deepfake Detector", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class PredictRequest(BaseModel):
    image_data: str   # base64-encoded image bytes
    threshold: float = 0.5


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/predict")
def predict(req: PredictRequest):
    try:
        raw = base64.b64decode(req.image_data)
        img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot decode image: {e}")

    arr = np.array(img)
    boxes, probs, _ = face_detector.detect(img, landmarks=True)

    crops: List[Image.Image] = []
    if boxes is not None:
        for box, conf in zip(boxes, probs):
            if conf is None or conf < FACE_THRESHOLDS[2]:
                continue
            crop = _square_crop(arr, box)
            if crop.size:
                crops.append(Image.fromarray(crop))

    if not crops:
        crops = [img]

    total_w = sum(w for *_, w in models)
    weighted = 0.0
    for proc, net, fake_idx, weight in models:
        inputs = proc(images=crops, return_tensors="pt").to(device)
        with torch.no_grad():
            logits = net(**inputs).logits
            probs_t = torch.softmax(logits, dim=-1)
        score = float(np.median(probs_t[:, fake_idx].cpu().numpy()))
        weighted += score * weight
    probability = weighted / total_w

    is_fake = probability >= req.threshold
    return {
        "probability": probability,
        "prediction": 1 if is_fake else 0,
        "class": "fake" if is_fake else "real",
        "model": "ensemble",
        "inference_time": 0.0,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
