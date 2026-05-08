# Verit — AI Detection Orchestrator

A thin orchestration layer over two existing detection backends:

- **DeepSafe** → image detection (assumed already running)
- **AI-Generated-Video-Detector** → video detection (wrapped here as a microservice)

The two detector codebases are **never modified or merged**. This app adds:
1. A FastAPI orchestrator (`backend/`) with a single `/detect` endpoint
2. A thin FastAPI wrapper (`video-service/`) that calls the video detector via a mounted volume
3. A React + Tailwind frontend (`frontend/`)

---

## Folder structure

```
ai-detection-app/
├── frontend/           React + Vite + Tailwind UI
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── index.css
│   │   └── components/
│   │       ├── FileUploader.jsx
│   │       └── ResultCard.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── nginx.conf
│   └── Dockerfile
├── backend/            FastAPI orchestrator
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── video-service/      FastAPI wrapper around AI-Generated-Video-Detector
│   ├── server.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## How requests flow

```
Browser → Frontend (port 3000)
        → /api proxy → Backend (port 8080)
                     → image: DEEPSAFE_URL/detect    (default localhost:8000)
                     → video: video-service:5005/predict
                                 └─ imports AI-Generated-Video-Detector/inference_2.py
```

Backend always returns this unified JSON:
```json
{
  "type": "image" | "video",
  "verdict": "AI" | "Real",
  "ai_probability": 0.0,
  "confidence": 0.0,
  "service": "deepsafe" | "video-detector",
  "details": { ... }
}
```

---

## Prerequisites

- Docker + Docker Compose
- The two detector repos already cloned and weights in place:
  - `../DeepSafe/` — running its own docker-compose stack (so the API is reachable)
  - `../AI-Generated-Video-Detector/` — code present, `checkpoints/model.pth` and `checkpoints/efficientnet.onnx` downloaded

---

## Run with Docker Compose

From inside this folder:

```bash
# 1. Make sure DeepSafe is running (separately):
#    cd ../DeepSafe && docker compose up -d
#    DeepSafe API will be on host port 8000.

# 2. Start this app's stack:
docker compose up -d --build

# 3. Open the UI:
#    http://localhost:3000
```

### Environment overrides

Set in your shell or a `.env` next to `docker-compose.yml`:

| Variable | Default | What it does |
|---|---|---|
| `DEEPSAFE_URL` | `http://host.docker.internal:8000` | Where the DeepSafe API lives. Change to `http://host.docker.internal:5004` if you've remapped DeepSafe's port. |
| `VIDEO_DETECTOR_PATH` | `../AI-Generated-Video-Detector` | Host path to the video detector repo (mounted into `video-service`). |

> **Note about DeepSafe's port.** The DeepSafe orchestrator API listens on **8000** by default; port 5004 inside that stack is the `universalfakedetect` single image model, not the user-facing API. If you want the full DeepSafe ensemble, point `DEEPSAFE_URL` at port 8000. If you genuinely want to call only that single model, point at 5004 and the response shape still works.

---

## Run without Docker (local dev)

Three terminals:

**1. Video service**
```bash
cd video-service
pip install -r requirements.txt
DETECTOR_PATH=../../AI-Generated-Video-Detector \
  uvicorn server:app --host 0.0.0.0 --port 5005
```

**2. Backend orchestrator**
```bash
cd backend
pip install -r requirements.txt
DEEPSAFE_URL=http://localhost:8000 \
  VIDEO_URL=http://localhost:5005 \
  uvicorn main:app --host 0.0.0.0 --port 8080
```

**3. Frontend**
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000 — Vite proxies /api → http://localhost:8080
```

---

## API

### `POST /detect`
Multipart file upload. Auto-detects image vs. video by content type or extension.

```bash
curl -X POST http://localhost:8080/detect \
  -F "file=@sample.jpg"
```

### `GET /health`
Returns reachability of each downstream service:
```json
{ "services": { "orchestrator": "healthy", "deepsafe": "healthy", "video": "healthy" } }
```

---

## Error handling

| Situation | HTTP | What you see |
|---|---|---|
| File is not image or video | 415 | "Unsupported file type" |
| Empty file | 400 | "Uploaded file is empty" |
| Downstream service unreachable | 503 | "X detection service is unreachable at URL" |
| Downstream timeout | 504 | "X detection service timed out after Ns" |
| Downstream returned non-JSON / 5xx | 502 | "X service error: ..." |

---

## Notes on the design

- **No code merging.** The video detector folder is mounted read-only and imported by the wrapper. The DeepSafe project is treated as an external HTTP API.
- **Single entry point.** Frontend only knows one URL (`/api/detect`). The backend hides which service is downstream.
- **Replaceable services.** Swap either downstream by changing one env var — no frontend or orchestrator code change needed.
