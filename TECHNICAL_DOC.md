# Verit — AI Detection Platform: Technical Documentation

## Overview

Verit is a full-stack web application that detects whether an image or video is AI-generated (deepfake). A user uploads a file in the browser; the frontend sends it to an orchestrator backend, which routes it to the appropriate AI model service, and returns a verdict with a confidence score.

---

## Architecture

```
Browser (React SPA)
        │  multipart/form-data POST /detect
        ▼
Orchestrator Backend (FastAPI — port 8080)
        │
        ├─── image ──► DeepSafe Image Service (FastAPI — port 5001)
        │                   └─ single HuggingFace deepfake classifier
        │
        └─── video ──► Video Detector Service (FastAPI — port 5005)
                            └─ AI-Generated-Video-Detector (EfficientNetV2 ONNX ensemble)
```

All four processes run locally (no Docker required for development). The browser talks only to the orchestrator; the model services are internal.

---

## Service Details

### 1. Frontend — React SPA (`frontend/`)

**Stack:** React 18, Vite, Tailwind CSS v3, Axios, Lucide React

#### State management (`src/App.jsx`)

All application state lives in the root component:

| State | Type | Purpose |
|---|---|---|
| `mode` | `'image' \| 'video'` | Which detection mode is active |
| `file` | `File \| null` | The file the user selected |
| `loading` | `boolean` | True while the API call is in-flight |
| `result` | `object \| null` | Normalized response from the backend |
| `error` | `string \| null` | Human-readable error message |

Switching tabs (`mode`) clears file, result, and error via a `useEffect`.

#### API call (`onAnalyze`)

```js
const form = new FormData();
form.append('file', file);
const { data } = await axios.post(`${API_BASE}/detect`, form, { timeout: 600_000 });
setResult(data);
```

`API_BASE` resolves to:
- **Development:** `http://localhost:8080` (Vite dev server proxies `/api` → `localhost:8080`)
- **Production:** `/api` (Nginx proxies `/api` → the orchestrator container)

The 600-second timeout exists because video analysis (frame extraction + model inference) can take 1–3 minutes.

#### Component tree

```
App
├── Header              — sticky navbar, logo, nav links
├── Hero                — heading, tab picker, UploadBox, ResultCard, error display
│   ├── Tabs            — Image / Video pill selector
│   ├── UploadBox       — drag-drop or click-to-browse, file preview, Analyze button
│   └── ResultCard      — verdict, confidence bar, raw JSON toggle
├── SampleGallery       — example media with hover overlays
├── Stats               — accuracy metrics (static display)
├── UseCases            — use-case cards with imagery
├── SupportedModels     — model capability table
├── DemoResult          — static example of what a result looks like
├── FAQ                 — accordion with grid-template-rows animation trick
├── CTASection          — bottom call-to-action, scrolls to hero
└── Footer
```

#### File upload flow (`UploadBox.jsx`)

1. User either drags a file onto the drop zone or clicks it (which opens `<input type="file">`).
2. `acceptsType()` checks MIME type and file extension against the current mode (image or video).
3. `onFileSelected(f)` bubbles the `File` object up to `App` state.
4. A `useEffect` watching `file` creates an object URL (`URL.createObjectURL`) for the preview, and revokes it on cleanup.
5. The file-loaded view shows a `<video>` or `<img>` preview, filename, size, MIME type, and the **Run detection** button.
6. While `loading` is true, a shimmer progress bar appears at the bottom of the card.

#### Result display (`ResultCard.jsx`)

```
verdict = "AI"  →  rose color palette
verdict = "Real" →  emerald color palette
```

The confidence bar animates via a CSS custom property:

```css
/* keyframe */
@keyframes progress {
  from { width: 0% }
  to   { width: var(--bar-w, 100%) }
}
```

The bar element receives `style={{ '--bar-w': `${pct}%`, width: `${pct}%` }}`. The `width` is the end state for browsers that don't trigger the animation; `--bar-w` drives the keyframe.

A `<details>` element at the bottom lets the user expand the raw JSON response from the backend.

---

### 2. Orchestrator Backend (`backend/main.py`)

**Stack:** Python 3.11+, FastAPI, httpx (async HTTP client), Pydantic, Uvicorn

The orchestrator is stateless. It accepts a file, decides whether it is image or video, calls the correct downstream service, normalizes the response shape, and returns a unified JSON object.

#### Media type detection

```python
def detect_media_type(file: UploadFile) -> Optional[str]:
    # 1. Check content_type header
    # 2. Fall back to file extension
    # Returns "image", "video", or None (→ 415 error)
```

#### Routing logic

```
file uploaded
    │
    ├─ image ─► DEEPSAFE_MODE == "single_model"?
    │               YES → base64-encode payload → POST JSON to {DEEPSAFE_URL}/predict
    │               NO  → forward multipart to {DEEPSAFE_URL}/detect
    │
    └─ video ─► forward multipart to {VIDEO_URL}/predict
```

Environment variables:

| Variable | Default | Meaning |
|---|---|---|
| `DEEPSAFE_URL` | `http://localhost:5001` | Base URL of the image detection service |
| `DEEPSAFE_MODE` | `single_model` | `single_model` = JSON/base64 API; `orchestrator` = multipart API |
| `VIDEO_URL` | `http://localhost:5005` | Base URL of the video detection service |
| `REQUEST_TIMEOUT` | `600` | Seconds before the downstream call times out |

#### Response normalization

Two upstream response shapes are unified into one:

**DeepSafe single-model `/predict`:**
```json
{ "probability": 0.87, "prediction": 1, "class": "fake", "model": "...", "inference_time": 2.3 }
```

**DeepSafe orchestrator `/detect`:**
```json
{ "is_likely_deepfake": true, "deepfake_probability": 0.87, "model_count": 3, "fake_votes": 2, "real_votes": 1 }
```

Both normalize to:
```json
{
  "type": "image",
  "verdict": "AI",
  "ai_probability": 0.87,
  "confidence": 0.87,
  "service": "deepsafe",
  "details": { ... }
}
```

For **video**, the video service already returns `ai_probability` and the orchestrator just re-wraps:
```json
{
  "type": "video",
  "verdict": "AI",
  "ai_probability": 0.73,
  "confidence": 0.73,
  "service": "video-detector",
  "details": { "raw_verdict": "FAKE", "raw_confidence": 0.735, "raw_text": "..." }
}
```

`confidence` = `ai_probability` when verdict is AI; `1 - ai_probability` when verdict is Real (distance from the fake threshold).

#### Error handling

All downstream errors are mapped to appropriate HTTP status codes:

| Condition | Status |
|---|---|
| Unsupported file type | 415 |
| Empty file | 400 |
| Service unreachable (ConnectError) | 503 |
| Timeout | 504 |
| Other network error | 502 |
| Downstream returned 4xx/5xx | 502 (with upstream detail) |
| Downstream returned non-JSON | 502 |

The `/health` endpoint pings both downstream services and returns their status, useful for diagnostics.

---

### 3. DeepSafe Image Service (`DeepSafe/` — port 5001)

**Stack:** Python, FastAPI, PyTorch, HuggingFace Transformers, MTCNN (facenet-pytorch)

DeepSafe is started with `deepsafe serve --manifest model.yaml`. The SDK spins up a FastAPI server that loads the configured model class (here: `CrossEfficientViTDetector`) and exposes `/predict`.

#### Request format

```json
POST /predict
{
  "image_data": "<base64-encoded image bytes>",
  "threshold": 0.5
}
```

The orchestrator base64-encodes the raw file bytes before sending.

#### CrossEfficientViTDetector model (`models/video/cross_efficient_vit/detector.py`)

Despite the name inherited from the original file, this is now an ensemble image classifier.

**Startup (`load()`):**
1. Loads two HuggingFace models:
   - `prithivMLmods/Deep-Fake-Detector-Model` (weight 0.6)
   - `prithivMLmods/Deep-Fake-Detector-v2-Model` (weight 0.4)
2. For each model, resolves which output label index corresponds to "fake" / "deepfake" by scanning the model's `id2label` mapping.
3. Initializes an MTCNN face detector (facenet-pytorch) to locate faces in each frame.

**Inference (`predict()`):**
1. Decodes the base64 image bytes → PIL Image.
2. Detects faces with MTCNN → extracts square-cropped face regions.
3. If no faces are found, falls back to running inference on the full image.
4. Each face crop is passed through each model's `AutoImageProcessor` → model forward pass → softmax → fake-label probability.
5. Per model: takes the median probability across all face crops (for outlier robustness).
6. Final probability: `0.6 × model_1_score + 0.4 × model_2_score` (weighted average).
7. Returns a `PredictionResult` via `make_result(probability, threshold)`.

---

### 4. Video Detector Service (`video-service/server.py` — port 5005)

**Stack:** Python, FastAPI, ONNX → PyTorch (onnx2pytorch), EfficientNetV2

This service is a thin FastAPI wrapper around the `AI-Generated-Video-Detector` library (`inference_2.py`).

#### Startup quirk

`inference_2.py` runs `argparse.parse_known_args()` at **import time** and asserts that no extra arguments exist. When Uvicorn starts, its own command-line arguments (`--host`, `--port`, etc.) are in `sys.argv`, which causes an `AssertionError`. The fix:

```python
_saved_argv = sys.argv
sys.argv = [sys.argv[0]]          # hide uvicorn args from argparse
try:
    from inference_2 import deepfakes_video_predict
finally:
    sys.argv = _saved_argv        # restore for uvicorn itself
```

`os.chdir(DETECTOR_PATH)` is also required because `inference_2.py` loads model checkpoints using hardcoded relative paths (e.g., `./checkpoints/efficientnet.onnx`).

#### Inference pipeline (inside `inference_2.py`)

1. Loads `efficientnet.onnx` and converts it to a PyTorch module via `onnx2pytorch`.
2. Receives a video file path.
3. Extracts frames at regular intervals using OpenCV.
4. Detects faces per frame (MTCNN or similar).
5. Passes face crops through EfficientNetV2.
6. Aggregates per-frame scores into a final verdict string:
   ```
   "The video is FAKE. \nConfidence score is: 73.521%"
   ```

#### Response parsing (`parse_result`)

```python
VERDICT_RE = re.compile(
    r"is\s+(REAL|FAKE).*?Confidence score is:\s*([\d.]+)",
    re.IGNORECASE | re.DOTALL,
)
```

- Extracts `REAL`/`FAKE` and the numeric confidence.
- Converts to `ai_probability`: if FAKE → score/100; if REAL → 1 − score/100.

#### Request/response

```
POST /predict  (multipart, field "file")
→ { "ai_probability": 0.735, "details": { "raw_verdict": "FAKE", "raw_confidence": 0.735, "raw_text": "..." } }
```

The video file is written to a `tempfile`, passed to `deepfakes_video_predict()`, then deleted in a `finally` block regardless of success or failure.

---

## Data Flow: End-to-End Example (Image)

```
1. User selects "photo.jpg" in the browser
2. UploadBox creates an object URL for the preview <img>
3. User clicks "Run detection"
4. App.jsx builds FormData({ file: photo.jpg })
5. axios.post("http://localhost:8080/detect", form)
6. Orchestrator reads the file bytes (JPEG)
7. detect_media_type() → "image"
8. base64.b64encode(bytes).decode("ascii") → b64_str
9. httpx.post("http://localhost:5001/predict", json={ image_data: b64_str, threshold: 0.5 })
10. DeepSafe decodes base64 → PIL Image → MTCNN face detection
11. Face crops → HuggingFace model ensemble → weighted probability
12. DeepSafe returns { probability: 0.87, prediction: 1, ... }
13. Orchestrator normalize_image_response() → { verdict: "AI", ai_probability: 0.87, confidence: 0.87, ... }
14. axios receives { verdict: "AI", confidence: 0.87, ... }
15. setResult(data) triggers ResultCard render
16. ResultCard shows "Likely AI-generated", rose progress bar at 87%
```

## Data Flow: End-to-End Example (Video)

```
1. User selects "clip.mp4" in the browser
2. User clicks "Run detection" (shimmer bar appears immediately)
3. axios.post("http://localhost:8080/detect", form, { timeout: 600000 })
4. Orchestrator: detect_media_type() → "video"
5. httpx.post("http://localhost:5005/predict", files={ file: ("clip.mp4", bytes, "video/mp4") })
6. Video service writes bytes to /tmp/tmpXXXX.mp4
7. deepfakes_video_predict("/tmp/tmpXXXX.mp4") runs (1–3 minutes)
   - Frame extraction via OpenCV
   - ONNX EfficientNetV2 inference per face crop
   - Aggregates scores → verdict string
8. parse_result() → { ai_probability: 0.265, details: { raw_verdict: "REAL", ... } }
9. normalize_video_response() → { verdict: "Real", ai_probability: 0.265, confidence: 0.735, ... }
10. Frontend shows "Likely real", emerald bar at 73%
```

---

## Startup (Local Development)

Four processes must be running simultaneously:

```powershell
# Terminal 1 — DeepSafe image service (port 5001)
cd e:\deepmedia\DeepSafe
.venv\Scripts\activate
deepsafe serve --manifest model.yaml --port 5001

# Terminal 2 — Video detector service (port 5005)
cd e:\deepmedia\ai-detection-app\video-service
.venv\Scripts\activate
$env:DETECTOR_PATH = "e:\deepmedia\AI-Generated-Video-Detector"
uvicorn server:app --host 0.0.0.0 --port 5005

# Terminal 3 — Orchestrator backend (port 8080)
cd e:\deepmedia\ai-detection-app\backend
.venv\Scripts\activate
$env:DEEPSAFE_URL = "http://localhost:5001"
$env:VIDEO_URL    = "http://localhost:5005"
uvicorn main:app --host 0.0.0.0 --port 8080

# Terminal 4 — React frontend (port 3000)
cd e:\deepmedia\ai-detection-app\frontend
npm run dev
```

The frontend Vite config proxies `/api/*` to `http://localhost:8080/*` so the browser can call the backend without CORS issues in development.

---

## Key Design Decisions

**Why base64 for images, multipart for videos?**
DeepSafe's single-model `/predict` endpoint was designed to accept JSON with a base64-encoded image. The video service was designed around Gradio/multipart conventions. The orchestrator bridges the gap.

**Why a separate video service?**
`AI-Generated-Video-Detector` is a research repo with a Gradio UI and module-level argparse that assumes direct script execution. Wrapping it in a FastAPI service isolates the startup quirks (argparse collision, relative paths, `os.chdir`) from the rest of the system and gives it a standard REST interface.

**Why two image models in an ensemble?**
A single model trained on one dataset has blind spots. The weighted ensemble (0.6 / 0.4 split) improves robustness across different generation methods (GAN, diffusion, face-swap). The weights reflect relative model performance on held-out test sets.

**Why median instead of mean for face aggregation?**
A video or high-resolution image may contain multiple faces. Using the mean would let a single noisy detection (occluded face, edge case) pull the score disproportionately. Median is more robust to such outliers.

**Why `gridTemplateRows` for the FAQ accordion?**
CSS `height: 0 → auto` transitions cannot be animated. The `grid-template-rows: 0fr → 1fr` trick works because `fr` units *can* be animated, and a grid child with `overflow: hidden` collapses naturally to 0 height when the row is `0fr`.

---

## File Structure

```
e:\deepmedia\ai-detection-app\
├── backend\
│   ├── main.py                  — FastAPI orchestrator
│   └── requirements.txt
├── video-service\
│   ├── server.py                — FastAPI wrapper for AI-Generated-Video-Detector
│   └── requirements.txt
├── frontend\
│   ├── src\
│   │   ├── App.jsx              — root, all state, API call
│   │   └── components\
│   │       ├── Header.jsx
│   │       ├── Hero.jsx         — hero section + tabs
│   │       ├── UploadBox.jsx    — drag-drop + preview
│   │       ├── ResultCard.jsx   — verdict display
│   │       ├── SampleGallery.jsx
│   │       ├── Stats.jsx
│   │       ├── UseCases.jsx
│   │       ├── SupportedModels.jsx
│   │       ├── DemoResult.jsx
│   │       ├── FAQ.jsx
│   │       ├── CTASection.jsx
│   │       └── Footer.jsx
│   ├── tailwind.config.js       — custom colors, animations, shadows
│   ├── index.html
│   └── package.json
└── docker-compose.yml           — containerized deployment (optional)

e:\deepmedia\DeepSafe\
└── models\video\cross_efficient_vit\
    └── detector.py              — HuggingFace ensemble image detector

e:\deepmedia\AI-Generated-Video-Detector\
└── inference_2.py               — EfficientNetV2 ONNX video inference
```
