# Ultra-small CPU-only YOLO + PyTorch base (~900 MB)
FROM ultralytics/ultralytics:latest-cpu

# Set working directory
WORKDIR /app

# Install Tesseract OCR & required libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy only your requirements that are NOT YOLO-related
COPY requirements.txt .

# IMPORTANT:
# Remove torch, torchvision, ultralytics, opencv-python from requirements.txt
# The base image already contains them optimized.

RUN sed -i '/torch/d' requirements.txt && \
    sed -i '/torchvision/d' requirements.txt && \
    sed -i '/ultralytics/d' requirements.txt && \
    sed -i '/opencv-python/d' requirements.txt

# Install remaining Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application with 5 workers for concurrent request handling
# -w 5: 5 worker processes (handles up to 5 concurrent requests)
# -k uvicorn.workers.UvicornWorker: Use Uvicorn worker class for async support
# --timeout 120: 120 second timeout for long-running YOLO inference
# --bind 0.0.0.0:8000: Listen on all interfaces
CMD ["gunicorn", "main:app", "-w", "5", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
