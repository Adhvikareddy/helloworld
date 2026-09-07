# Q-SENTINEL API Dockerfile
# Runs the FastAPI application hosting L1–L4 runtime layers.
# Build context: repository root (needs apps/, src/, requirements.txt)
#
# Base image: python:3.11-slim (official Docker Hub image)
# Reason: Qiskit 1.1.x requires Python ≥3.8, <3.13. Slim variant
#         minimises image size while providing a working C toolchain
#         for native dependencies (qiskit-aer).

FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt \
    && apt-get purge -y build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY src/ /app/src/
COPY apps/ /app/apps/

# Ensure data directory exists
RUN mkdir -p /app/data

# Non-root runtime user
RUN useradd -r -s /bin/false qsentinel \
    && chown -R qsentinel:qsentinel /app
USER qsentinel

ENV PYTHONPATH=/app
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
