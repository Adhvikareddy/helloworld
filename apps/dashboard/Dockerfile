# Q-SENTINEL Dashboard Dockerfile
# Runs the Streamlit Judge Mode UI.
# Build context: repository root (needs apps/, attacker/, requirements.txt)
#
# Base image: python:3.11-slim (official Docker Hub image)

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Dashboard needs apps/dashboard and attacker/ for the Judge Mode buttons
COPY apps/ /app/apps/
COPY attacker/ /app/attacker/
COPY src/ /app/src/

RUN mkdir -p /app/data

RUN useradd -r -s /bin/false qsentinel \
    && chown -R qsentinel:qsentinel /app
USER qsentinel

ENV PYTHONPATH=/app
EXPOSE 8501

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "apps/dashboard/app.py", \
     "--server.port=8501", "--server.address=0.0.0.0", \
     "--server.headless=true"]
