---
title: Verit Image AI
emoji: 🖼️
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Verit Image AI — DeepSafe NPR detector

FastAPI service for AI-generated image detection.
Uses DeepSafe's `npr_deepfakedetection` model (ResNet-50 on Neighbor Pixel Relations features).

POST `/predict` with JSON body:
```json
{ "image_data": "<base64>", "threshold": 0.5 }
```
