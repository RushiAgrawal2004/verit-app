---
title: Verit Image AI (Strong)
emoji: 🔬
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Verit Image AI — Strong detector (2-model ensemble)

Modern multi-model AI-image detector for the Verit ensemble. Combines two
complementary classifiers via in-Space averaging:

- `Organika/sdxl-detector` — Swin Transformer fine-tuned on SDXL/Wikimedia
  pairs. Strong on Stable Diffusion family (SD, SDXL, SD3, FLUX share
  similar artifacts).
- `Ateeqq/ai-vs-human-image-detector` — SigLIP vision model trained on
  120k AI/human pairs. Different architecture → diversity. Robust to
  re-compression and screenshot artifacts.

POST `/predict` with JSON body:
```json
{ "image_data": "<base64>", "threshold": 0.5 }
```

Returns:
```json
{
  "probability": 0.78,
  "prediction": 1,
  "class": "fake",
  "model": "ensemble[sdxl-detector,ai-vs-human-image-detector]",
  "inference_time": 1.21,
  "components": [
    {"model":"Organika/sdxl-detector","probability":0.82,"weight":0.5},
    {"model":"Ateeqq/ai-vs-human-image-detector","probability":0.74,"weight":0.5}
  ]
}
```

Per-model weights can be tuned without rebuilding by setting Space-secret
env vars (e.g. `WEIGHT_ORGANIKA_SDXL_DETECTOR=0.7`,
`WEIGHT_ATEEQQ_AI_VS_HUMAN_IMAGE_DETECTOR=0.3`). Set to `0` to fully
disable a model.
