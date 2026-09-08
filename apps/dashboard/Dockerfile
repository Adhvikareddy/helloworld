# Q-SENTINEL v9 — Dashboard Dockerfile
# Track B: Streamlit Judge Mode UI

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN groupadd -r qsentinel && useradd -r -g qsentinel -u 1000 qsentinel

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir streamlit pandas

COPY src/ ./src/
COPY apps/ ./apps/
COPY experiments/ ./experiments/
COPY data/ ./data/

RUN mkdir -p /app/data && chown -R qsentinel:qsentinel /app/data

USER qsentinel

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "apps/dashboard/app.py", \
     "--server.port=8501", "--server.address=0.0.0.0", \
     "--server.headless=true"]
