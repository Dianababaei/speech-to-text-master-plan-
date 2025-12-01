# ============================================================================
# Builder Stage: Install dependencies and build artifacts
# ============================================================================
FROM python:3.11-slim as builder

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies needed for building Python packages
# gcc, g++: For compiling C extensions
# libpq-dev: For PostgreSQL adapter (psycopg2)
# curl: For health checks and utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files first for better layer caching
# This ensures dependencies are only reinstalled when these files change
COPY requirements.txt* pyproject.toml* poetry.lock* ./

# Install Python dependencies
# Support both requirements.txt and pyproject.toml (Poetry/pip)
RUN if [ -f "requirements.txt" ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    elif [ -f "pyproject.toml" ]; then \
        pip install --no-cache-dir poetry && \
        poetry config virtualenvs.create false && \
        poetry install --no-dev --no-interaction --no-ansi; \
    else \
        echo "No dependency file found. Installing base FastAPI dependencies." && \
        pip install --no-cache-dir fastapi uvicorn[standard] python-multipart; \
    fi

# ============================================================================
# Runtime Stage: Minimal production image
# ============================================================================
FROM python:3.11-slim as runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Install only runtime system dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
# UID 1000 is standard for first non-root user
RUN groupadd -r appuser -g 1000 && \
    useradd -r -u 1000 -g appuser -s /bin/bash -m appuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser . .

# Ensure proper ownership and permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose FastAPI default port
EXPOSE 8000

# Health check (optional but recommended)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the FastAPI application with uvicorn
# --host 0.0.0.0: Listen on all network interfaces
# --port 8000: Default FastAPI port
# --workers: Number of worker processes (can be overridden via environment variable)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
