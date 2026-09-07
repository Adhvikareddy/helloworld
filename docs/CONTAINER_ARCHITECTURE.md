# Q-SENTINEL Container Architecture

## Overview

Q-SENTINEL is deployed as four containers on an isolated Docker bridge
network.  Three are custom-built; one uses an upstream image.

```
                         HOST MACHINE
                              │
              ┌───────────────┼───────────────┐
              │               │               │
        :8501 (Dashboard)   :3389 (RDP)       │ (no other host ports)
              │               │               │
══════════════╪═══════════════╪═══════════════╪══════════════
              │     qsentinel_internal        │
              │         (bridge)              │
              │                               │
  ┌───────────┴───────────┐   ┌───────────────┴────────────┐
  │   qsentinel-dashboard │   │      qsentinel-rdp         │
  │   Streamlit :8501     │   │   XFCE desktop :3000       │
  │   Judge Mode UI       │   │   Browser + Terminal       │
  └───────────┬───────────┘   └────────────────────────────┘
              │ http://qsentinel-api:8000
              │
  ┌───────────┴───────────┐
  │    qsentinel-api      │
  │    FastAPI :8000      │   ←── SQLite volume (qsentinel_data)
  │    L3 → L1 → L2 → L4 │
  └───────────┬───────────┘
              │ http://qsentinel-api:8000
              │
  ┌───────────┴───────────┐
  │  qsentinel-attacker   │
  │  Adversarial client   │   ←── SQLite volume (shared, for ledger tamper)
  │  python -m attacker   │
  └───────────────────────┘
```

## Container Details

### qsentinel-api

| Property | Value |
|---|---|
| Dockerfile | `apps/api/Dockerfile` |
| Build context | Repository root (`.`) |
| Base image | `python:3.11-slim` (official Docker Hub) |
| Runtime user | `qsentinel` (non-root) |
| Internal port | 8000 |
| Host port | None (internal only) |
| Volumes | `qsentinel_data:/app/data` |
| Network | `qsentinel_internal` |
| Healthcheck | `curl -f http://localhost:8000/v1/health` |
| Responsibility | Runs the FastAPI application hosting all four runtime layers: L3 (Security), L1 (QDS/Qiskit-Aer), L2 (Statistics), L4 (Ledger). |

### qsentinel-dashboard

| Property | Value |
|---|---|
| Dockerfile | `apps/dashboard/Dockerfile` |
| Build context | Repository root (`.`) |
| Base image | `python:3.11-slim` |
| Runtime user | `qsentinel` (non-root) |
| Internal port | 8501 |
| Host port | 8501 |
| Volumes | None |
| Network | `qsentinel_internal` |
| Healthcheck | `curl -f http://localhost:8501/_stcore/health` |
| Environment | `QSENTINEL_API_URL=http://qsentinel-api:8000` |
| Responsibility | Streamlit Judge Mode UI. Each button invokes real attacker scenario code. |

### qsentinel-attacker

| Property | Value |
|---|---|
| Dockerfile | `services/attacker/Dockerfile` |
| Build context | Repository root (`.`) |
| Base image | `python:3.11-slim` |
| Runtime user | `attacker` (non-root) |
| Internal port | None |
| Host port | None |
| Volumes | `qsentinel_data:/app/data` (for ledger tamper experiment) |
| Network | `qsentinel_internal` |
| Environment | `QSENTINEL_API_URL`, `QSENTINEL_DB_PATH` |
| Responsibility | Adversarial test client. Attacks are executed via `docker compose exec` or the dashboard. |

### qsentinel-rdp

| Property | Value |
|---|---|
| Image | `lscr.io/linuxserver/webtop:ubuntu-xfce` |
| Source | [LinuxServer.io Webtop](https://docs.linuxserver.io/images/docker-webtop/) |
| Host port | 3389 → 3000 (internal) |
| Volumes | None |
| Network | `qsentinel_internal` |
| Responsibility | Lightweight XFCE desktop accessible via browser. For judge/operator inspection only. Does NOT run Q-SENTINEL logic. No Docker socket access. |

## Network

| Name | Driver | Purpose |
|---|---|---|
| `qsentinel_internal` | bridge | Isolated network for all Q-SENTINEL services |

- No host networking.
- No hardcoded container IPs.
- Services discover each other by Compose service name (DNS).
- Only `qsentinel-dashboard` (8501) and `qsentinel-rdp` (3389) expose host ports.
- The API is intentionally internal-only.

## Volume

| Name | Mount | Contents |
|---|---|---|
| `qsentinel_data` | `/app/data` | SQLite ledger (`ledger.db`), calibration baseline (`baseline.json`), thresholds (`thresholds.json`) |

This volume is shared between `qsentinel-api` and `qsentinel-attacker`:
- The API writes ledger events and calibration data.
- The attacker reads the ledger DB for the tamper experiment.

## Security Boundaries

- No container runs as root at runtime (except `qsentinel-rdp` which is an upstream image).
- No container has access to the Docker socket.
- No container runs in privileged mode.
- The attacker communicates with the API through HTTP over the internal network — it never modifies Python state directly.
- Only `qsentinel-rdp` exposes a human-facing port (3389→3000).

## Image Selection Rationale

| Image | Tag | Source | Reason |
|---|---|---|---|
| `python` | `3.11-slim` | [Docker Hub](https://hub.docker.com/_/python) | Official Python image. 3.11 is required because qiskit-aer 0.14.x needs Python <3.13. Slim variant minimises size. |
| `linuxserver/webtop` | `ubuntu-xfce` | [LinuxServer.io](https://docs.linuxserver.io/images/docker-webtop/) | Well-maintained community image with lightweight XFCE desktop and web-based access. Used for judge interaction only. |
