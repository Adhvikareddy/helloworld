# Q-SENTINEL Docker Operations Guide

This document explains how to build, start, operate, stop, inspect, and test
the Q-SENTINEL system using Docker Compose.

---

## Prerequisites

| Requirement | Minimum | Notes |
|---|---|---|
| Docker Engine | 24.0+ | `docker --version` to verify |
| Docker Compose | v2 (plugin) | Bundled with Docker Desktop; `docker compose version` |
| RAM | 4 GB free | Qiskit-Aer simulation + 4 containers |
| Disk | 5 GB free | Docker images + build cache |
| Ports available | 8501, 3389 | Dashboard and RDP respectively |

> **Docker must be installed before executing any deployment command.**

### Installing Docker

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# Log out and back in for group membership to take effect
```

**Windows:**
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) (requires WSL2 backend).
2. Enable WSL2 integration in Docker Desktop → Settings → Resources → WSL Integration.
3. Open a WSL2 terminal or PowerShell to run commands.

**macOS:**
1. Install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/).
2. Use the integrated terminal.

---

## Build

```bash
docker compose build
```

This builds three custom images:

| Service | Dockerfile | What it contains |
|---|---|---|
| `qsentinel-api` | `apps/api/Dockerfile` | FastAPI + Qiskit-Aer + L1/L2/L3/L4 |
| `qsentinel-dashboard` | `apps/dashboard/Dockerfile` | Streamlit Judge Mode |
| `qsentinel-attacker` | `services/attacker/Dockerfile` | Adversarial test client |

The fourth service (`qsentinel-rdp`) uses a pre-built upstream image and does not require building.

---

## Start

```bash
docker compose up -d
```

Detached mode (`-d`) runs containers in the background.  The API service
must become healthy before the dashboard and attacker start (enforced via
`depends_on: condition: service_healthy`).

---

## Check Status

```bash
docker compose ps
```

All services should show `Up` or `Up (healthy)`.

### Health Checks

| Service | Endpoint | Interval |
|---|---|---|
| `qsentinel-api` | `GET /v1/health` | 10s |
| `qsentinel-dashboard` | `GET /_stcore/health` | 15s |

---

## Logs

```bash
# All services
docker compose logs --tail=50

# Specific service
docker compose logs --tail=100 qsentinel-api
docker compose logs --tail=100 qsentinel-attacker
docker compose logs --tail=100 qsentinel-dashboard
docker compose logs --tail=100 qsentinel-rdp
```

---

## Access

| Interface | URL | Notes |
|---|---|---|
| Dashboard (Judge Mode) | `http://localhost:8501` | Direct from host browser |
| RDP / Webtop | `http://localhost:3389` | Lightweight XFCE desktop |
| API docs (Swagger) | `http://localhost:8501` → internal `http://qsentinel-api:8000/docs` | From inside RDP browser |
| API (internal only) | `http://qsentinel-api:8000` | Not exposed to host |

> The API is intentionally **not** exposed on the host.  Access it through
> the dashboard, attacker, or from inside the RDP container's browser.

---

## Judge Mode

1. Open `http://localhost:8501` in your browser.
2. Ensure **🔴 LIVE EXPERIMENT** mode is selected.
3. Click buttons in this order:

| Step | Button | Expected | Layer |
|---|---|---|---|
| 1 | ✅ LEGITIMATE | ACCEPT | L1/L2 |
| 2 | 🔴 FORGERY | REJECT (invalid_qds_signature) | L1 |
| 3 | 🔁 REPLAY | REJECT (replay detected) | L3 |
| 4 | 🎭 IMPERSONATION | REJECT (identity binding) | L3 |
| 5 | 🚫 UNAUTHORIZED | REJECT (unauthorized verifier) | L3 |
| 6 | 📡 CHANNEL | QUARANTINE/REJECT (statistical) | L2 |
| 7 | 🔗 TAMPER LEDGER | Integrity violation | L4 |
| 8 | 🔍 VERIFY CHAIN | Shows chain status | L4 |

Each button executes real code against the running API — not pre-recorded demos.

---

## Attack CLI

All attack commands run inside the `qsentinel-attacker` container:

```bash
# Run all attacks
make attack-all

# Individual attacks
make attack-forgery-a       # Invalid-signature mutation → L1 REJECT
make attack-forgery-b       # Valid-path forgery experiment → L1/L2 measured
make attack-replay           # Reused nonce → L3 REJECT
make attack-impersonation   # Wrong signer identity → L3 REJECT
make attack-unauthorized    # Unregistered verifier → L3 REJECT
make attack-channel          # Quantum disturbance → L2 QUARANTINE/REJECT
make attack-ledger           # Tamper SQLite → L4 integrity violation

# Advanced: custom parameters
docker compose exec qsentinel-attacker \
    python -m attacker.runner --attack channel --level high --shots 4096 --count 10
```

---

## Calibration

The Q-SENTINEL spec requires:

```
CALIBRATION → VALIDATION → FREEZE → BLIND TEST
```

**No blind-test result may be used to tune thresholds.**

```bash
# Run calibration and freeze thresholds
make calibrate

# Verify calibration status
docker compose exec qsentinel-api \
    python -c "from src.detection.policy import DecisionPolicy; p=DecisionPolicy(); print(p.get_thresholds())"

# Run blind evaluation (thresholds must already be frozen)
make blind
```

---

## Verify Ledger

```bash
make verify-ledger
```

This calls `GET /v1/ledger/verify-chain` and prints the result.

---

## Shutdown

```bash
# Stop containers (preserves volumes)
docker compose down

# Stop AND remove persistent data (SQLite, calibration, experiments)
docker compose down -v
```

> ⚠️ `docker compose down -v` deletes the `qsentinel_data` volume containing
> the SQLite ledger, calibration state, and experiment results.  Use only
> for a full reset.

---

## Reset (Optional)

To completely reset the system to a clean state:

```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

> **Warning:** This deletes:
> - SQLite ledger database
> - Hash-chain evidence history
> - Frozen calibration baselines and thresholds
> - Experiment results

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `Cannot connect to Docker daemon` | Docker is not running | Start Docker Desktop or `sudo systemctl start docker` |
| Build fails on qiskit-aer | Missing C compiler in image | The API Dockerfile installs `build-essential` in a build stage |
| Port 8501 already in use | Another service on that port | `lsof -i :8501` and stop the conflicting process |
| Port 3389 already in use | Native RDP or another service | Change the host port in `docker-compose.yml` |
| API unhealthy | Startup crash or dependency issue | `docker compose logs qsentinel-api` |
| Dashboard shows "Connection Error" | API not yet healthy | Wait for API health check; `docker compose ps` |
| Attacker "Connection refused" | API not reachable | Verify both are on `qsentinel_internal` network |
| RDP blank screen | Image still downloading | Wait; `docker compose logs qsentinel-rdp` |
| Permission errors on /app/data | Volume ownership mismatch | Recreate volume: `docker compose down -v && docker compose up -d` |
| Stale results after code change | Old image cached | `docker compose build --no-cache` |
| Network resolution failure | DNS not working inside containers | Restart Docker: `docker compose down && docker compose up -d` |
