import os
import re
import sys
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

# inference_2.py uses relative paths (./checkpoints/) so we must be in the same dir
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# inference_2.py runs argparse at import time and asserts no extra argv
_saved = sys.argv
sys.argv = [sys.argv[0]]
try:
    from inference_2 import deepfakes_video_predict
finally:
    sys.argv = _saved

VERDICT_RE = re.compile(
    r"is\s+(REAL|FAKE).*?Confidence score is:\s*([\d.]+)",
    re.IGNORECASE | re.DOTALL,
)

app = FastAPI(title="Video Detector Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


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
def health():
    return {"status": "healthy"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
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
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return parse_result(result_text)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
