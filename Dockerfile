# Multi-stage Dockerfile for speech-to-text transcription service
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY requirements.txt* ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -e .

# Copy application code
COPY app/ ./app/

# Create directories for uploads
RUN mkdir -p /app/uploads

# Expose port for API (if running API server)
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["python", "-m", "app.workers.transcription_worker"]
