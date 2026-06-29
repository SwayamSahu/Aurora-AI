# Backend image — cross-platform (runs on Mac arm64 and Linux).
# Used for the API and the CPU/mock workers in development.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# FFmpeg for media processing; espeak-ng for CPU text-to-speech on Linux.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg espeak-ng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install app deps (base + cross-platform media). NOT gpu.txt.
COPY requirements/ requirements/
RUN pip install -r requirements/app.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
