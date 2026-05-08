FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 ffmpeg \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
        torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2 \
    && pip install --no-cache-dir -r requirements.txt

COPY server.py ./

ENV DETECTOR_PATH=/app/video-detector
EXPOSE 5005
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "5005"]
