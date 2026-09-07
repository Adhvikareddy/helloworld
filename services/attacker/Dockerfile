# Q-SENTINEL Attacker Dockerfile
# Dedicated adversarial test client for the isolated Q-SENTINEL testbed.
# Build context: repository root (needs attacker/, requirements.txt)
#
# Base image: python:3.11-slim (official Docker Hub image)

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Attacker needs only the attacker/ package and shared src/ for imports
COPY attacker/ /app/attacker/
COPY src/ /app/src/

RUN mkdir -p /app/data

RUN useradd -r -s /bin/false attacker \
    && chown -R attacker:attacker /app
USER attacker

ENV PYTHONPATH=/app

# Keep container alive for exec-based attack runs
CMD ["tail", "-f", "/dev/null"]
