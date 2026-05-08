import os
import re
import sys
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

# Path to the cloned AI-Generated-Video-Detector repo (mounted as volume in compose)
DETECTOR_PATH = os.environ.get("DETECTOR_PATH", "/app/video-detector")
if DETECTOR_PATH not in sys.path:
    sys.path.insert(0, DETECTOR_PATH)
os.chdir(DETECTOR_PATH)  # inference_2.py uses relative paths to checkpoints/

# inference_2.py parses argparse at import time and asserts no extra argv —
# stash uvicorn's argv away so the import succeeds, then restore it.
_saved_argv = sys.argv
sys.argv = [sys.argv[0]]
try:
    from inference_2 import deepfakes_video_predict  # noqa: E402
finally:
    sys.argv = _saved_argv

VERDICT_RE = re.compile(
    r"is\s+(REAL|FAKE).*?Confidence score is:\s*([\d.]+)",
    re.IGNORECASE | re.DOTALL,
)

app = FastAPI(title="Video Detector Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def parse_result(text: str) -> dict:
    match = VERDICT_RE.search(text)
    if not match:
        return {"ai_probability": 0.5, "raw": text}
    verdict = match.group(1).upper()
    score = float(match.group(2)) / 100.0
    ai_prob = score if verdict == "FAKE" else 1.0 - score
    return {
        "ai_probability": ai_prob,
        "details": {"raw_verdict": verdict, "raw_confidence": score, "raw_text": text.strip()},
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "video-detector"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not (file.content_type or "").startswith("video/") and not (file.filename or "").lower().endswith(
        (".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v")
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Expected a video file.",
        )

    suffix = os.path.splitext(file.filename or "")[1].lower() or ".mp4"
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file.")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(payload)
        tmp_path = tmp.name

    try:
        result_text = deepfakes_video_predict(tmp_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {type(exc).__name__}: {exc}",
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return parse_result(result_text)
