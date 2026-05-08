FROM python:3.11-slim

# system libs needed by opencv / torch / moviepy
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# install CPU-only torch FIRST (avoids huge CUDA download)
RUN pip install --no-cache-dir \
    torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0 \
    --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code and model checkpoints
COPY . .

EXPOSE 7860
CMD ["python", "app.py"]
