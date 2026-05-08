---
title: Verit Image AI
emoji: 🖼️
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Verit Image AI

FastAPI service for AI-generated image detection.
Uses an ensemble of HuggingFace deepfake classifiers + MTCNN face cropping.

POST `/predict` with JSON body:
```json
{ "image_data": "<base64>", "threshold": 0.5 }
```
