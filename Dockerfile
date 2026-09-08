# Q-SENTINEL v9 — API Service Dockerfile
# Track B: Production container (Python 3.11-slim for stability)
#
# Security:
#   - Non-root user (uid=1000)
#   - Read-only filesystem (except /app/data volume mount)
#   - No shell utilities (slim image)
#   - PYTHONDONTWRITEBYTECODE prevents .pyc writes

FROM python:3.11-slim AS base

LABEL maintainer="Q-SENTINEL Team"
LABEL version="9.0.0"

# Security: don't buffer output, don't write .pyc
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Create non-root user
RUN groupadd -r qsentinel && useradd -r -g qsentinel -u 1000 qsentinel

WORKDIR /app

# Install dependencies first (for layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir uvicorn[standard]

# Copy application code
COPY src/ ./src/
COPY apps/api/ ./apps/api/
COPY data/ ./data/

# Ensure data directory exists and is writable by qsentinel
RUN mkdir -p /app/data && chown -R qsentinel:qsentinel /app/data

# Switch to non-root user
USER qsentinel

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/v1/health')"

# Run with uvicorn
CMD ["python", "-m", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
