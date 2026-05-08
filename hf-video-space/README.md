---
title: Verit Video AI
emoji: 🎬
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Verit Video AI

FastAPI service for AI-generated video detection.
Wraps the AI-Generated-Video-Detector EfficientNet ONNX model.

POST `/predict` with multipart `file` field (video file).
