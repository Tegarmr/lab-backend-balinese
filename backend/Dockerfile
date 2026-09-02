FROM python:3.11-slim

# System dependencies for OpenCV and plantcv
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY seamformer/ ./seamformer/

# Create upload directory
RUN mkdir -p /app/uploads

# Weights will be mounted as volume
# COPY weights/ ./weights/

EXPOSE 8000

# Single worker to conserve memory on 2GB VPS
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--timeout-keep-alive", "300"]
