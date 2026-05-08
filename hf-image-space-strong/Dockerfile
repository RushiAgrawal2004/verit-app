FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Cache locations must be writable at runtime (HF Spaces runs as non-root).
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV HF_HUB_DISABLE_TELEMETRY=1

# CPU-only torch first
RUN pip install --no-cache-dir \
    torch==2.4.0 torchvision==0.19.0 \
    --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Pre-download model weights at build time so the first request is fast
# and Spaces' boot-health-check timeout is comfortable.
RUN python -c "from transformers import AutoImageProcessor, AutoModelForImageClassification; \
    AutoImageProcessor.from_pretrained('dima806/ai_vs_real_image_detection'); \
    AutoModelForImageClassification.from_pretrained('dima806/ai_vs_real_image_detection'); \
    print('weights cached')"

# Make the cache world-readable so the Spaces non-root runtime can read it.
RUN chmod -R a+rX /app/.cache

EXPOSE 7860
CMD ["python", "app.py"]
