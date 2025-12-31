# Multi-stage Dockerfile for efficient production builds
# This follows industry best practices for Python ML applications

# Stage 1: Builder stage (optional, for optimization)
# We use a single stage here for simplicity, but multi-stage builds
# can reduce final image size by excluding build dependencies

FROM python:3.11-slim

# Set working directory inside container
# All commands run from this directory
WORKDIR /app

# Set environment variables
# Prevents Python from writing .pyc files (saves space)
# Ensures output is unbuffered (logs appear immediately)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random

# Install system dependencies (if needed)
# Uncomment if you need additional system packages:
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc \
#     && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker layer caching optimization)
# Docker caches layers, so if requirements.txt doesn't change,
# we don't reinstall packages on every build
COPY requirements_api.txt .

# Install Python dependencies
# --no-cache-dir: Don't store cache (smaller image)
# --upgrade pip: Use latest pip
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements_api.txt

# Copy application code
# This is done after requirements to leverage Docker layer caching
# Code changes more frequently than dependencies
COPY app/ ./app/
COPY churn_prediction_model.pkl .

# Create non-root user for security (best practice)
# Running as root is a security risk in production
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port 8000 (default FastAPI/Uvicorn port)
EXPOSE 8000

# Health check (optional but recommended)
# Docker/Kubernetes can use this to check if container is healthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application
# Using uvicorn directly (production ASGI server)
# --host 0.0.0.0: Listen on all interfaces (required in containers)
# --port 8000: Port to listen on
# --workers 1: Single worker (increase for production with proper load balancing)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

