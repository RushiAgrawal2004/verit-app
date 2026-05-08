FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git wget libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# CPU-only torch first
RUN pip install --no-cache-dir \
    torch==2.4.0 torchvision==0.19.0 \
    --index-url https://download.pytorch.org/whl/cpu

# DeepSafe SDK: provides fastapi/uvicorn/pydantic/pyyaml/Pillow + the `deepsafe` CLI
COPY sdk/ /app/sdk/
RUN pip install --no-cache-dir /app/sdk/

# Extra deps for UniversalFakeDetect (CLIP needs ftfy/regex/tqdm)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Detector + manifest
COPY detector.py model.yaml ./

# Clone upstream UniversalFakeDetect repo (provides models.get_model)
RUN git clone https://github.com/WisconsinAIVision/UniversalFakeDetect.git universalfakedetect && \
    mkdir -p universalfakedetect/pretrained_weights

# Download CLIP ViT-L/14 weights (HF mirror with OpenAI fallback)
RUN mkdir -p /root/.cache/clip && \
    (wget -O /root/.cache/clip/ViT-L-14.pt \
        https://huggingface.co/siddharthksah/DeepSafe-weights/resolve/main/universalfakedetect/ViT-L-14.pt \
     || wget -O /root/.cache/clip/ViT-L-14.pt \
        https://openaipublic.azureedge.net/clip/models/b8cca3fd41ae0c99ba7e8951adf17d267cdb84cd88be6f7c2e0eca1737a03836/ViT-L-14.pt)

# Download FC head weights (HF mirror with upstream fallback)
RUN (wget -O universalfakedetect/pretrained_weights/fc_weights.pth \
        https://huggingface.co/siddharthksah/DeepSafe-weights/resolve/main/universalfakedetect/fc_weights.pth \
     || wget -O universalfakedetect/pretrained_weights/fc_weights.pth \
        https://github.com/WisconsinAIVision/UniversalFakeDetect/raw/main/pretrained_weights/fc_weights.pth)

# HF Spaces requires port 7860
ENV MODEL_PORT=7860
ENV USE_GPU=false
ENV PRELOAD_MODEL=true
ENV MODEL_TIMEOUT=0

EXPOSE 7860

CMD ["deepsafe", "serve", "--manifest", "model.yaml"]
