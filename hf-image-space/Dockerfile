FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git wget libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# CPU-only torch first (avoids huge CUDA wheels)
RUN pip install --no-cache-dir \
    torch==2.4.0 torchvision==0.19.0 \
    --index-url https://download.pytorch.org/whl/cpu

# DeepSafe SDK: provides fastapi/uvicorn/pydantic/pyyaml/Pillow + the `deepsafe` CLI
COPY sdk/ /app/sdk/
RUN pip install --no-cache-dir /app/sdk/

# Extra deps required by the NPR detector
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Detector code + model manifest
COPY detector.py model.yaml ./

# Clone upstream NPR-DeepfakeDetection (provides networks.resnet) and fetch weights.
# Falls back to upstream raw weights if the HF mirror is unavailable.
RUN git clone https://github.com/chuangchuangtan/NPR-DeepfakeDetection.git npr_deepfakedetection && \
    mkdir -p npr_deepfakedetection/weights && \
    (wget -O npr_deepfakedetection/weights/NPR.pth \
        https://huggingface.co/siddharthksah/DeepSafe-weights/resolve/main/npr_deepfakedetection/NPR.pth \
     || wget -O npr_deepfakedetection/weights/NPR.pth \
        https://github.com/chuangchuangtan/NPR-DeepfakeDetection/raw/main/model_epoch_last_3090.pth)

# HF Spaces requires port 7860
ENV MODEL_PORT=7860
ENV USE_GPU=false
ENV PRELOAD_MODEL=true
ENV MODEL_TIMEOUT=0

EXPOSE 7860

CMD ["deepsafe", "serve", "--manifest", "model.yaml"]
