---
title: Verit Image AI (UniversalFakeDetect)
emoji: 🧠
colorFrom: pink
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Verit Image AI — DeepSafe UniversalFakeDetect

Second image-detection service for the Verit ensemble.
Uses DeepSafe's `universalfakedetect` model (CLIP ViT-L/14 features + linear FC head).

POST `/predict` with JSON body:
```json
{ "image_data": "<base64>", "threshold": 0.5 }
```
