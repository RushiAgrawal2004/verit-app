---
title: Verit Image AI (Strong)
emoji: 🔬
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Verit Image AI — Strong detector

Modern ViT-based AI-image classifier for the Verit ensemble.
Wraps `dima806/ai_vs_real_image_detection` (ViT-base-patch16-224, ~340 MB)
in the same HTTP contract as the other image services.

POST `/predict` with JSON body:
```json
{ "image_data": "<base64>", "threshold": 0.5 }
```

Swap the underlying model by setting the `MODEL_ID` Space-secret to any
HuggingFace `image-classification` checkpoint with a binary AI/Real
output, then **Restart this Space**. No rebuild needed for the swap
itself — only for cold-cache pre-download speed.
