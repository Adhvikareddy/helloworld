# Q-SENTINEL v8

**Quantum-Inspired Threat Detection for Teleportation-Based Quantum Digital Signatures**

SIH 2026 · PS26141 · Egreen Quanta · Category: Software · Theme: Blockchain & Cybersecurity

---

## What is Q-SENTINEL?

Q-SENTINEL is a focused software framework for detecting threats in
teleportation-based Quantum Digital Signature (QDS) verification.  It uses
Qiskit-Aer simulation, deterministic statistical analysis, and classical
security controls — **no AI/ML**.

## Architecture

Four runtime layers execute in strict order:

```
UNTRUSTED REQUEST
        ↓
   L3 — Security & Authorization Guard
        ↓  (authorized + fresh)
   L1 — QDS Verification Core  (Qiskit-Aer)
        ↓  (measurement evidence)
   L2 — Statistical Threat Detector
        ↓
   ACCEPT / QUARANTINE / REJECT
        ↓
   L4 — Tamper-Evident Evidence Ledger  (SQLite hash-chain)
```

## Repository Structure

```
q-sentinel/
├── apps/
│   ├── api/             # FastAPI backend + Dockerfile
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── routes/
│   └── dashboard/       # Streamlit Judge Mode + Dockerfile
│       ├── Dockerfile
│       └── app.py
├── attacker/            # Adversarial test harness
│   ├── runner.py        # CLI orchestrator
│   ├── client.py        # HTTP client
│   ├── config.py        # Centralised configuration
│   ├── reporting.py     # Structured JSON results
│   └── scenarios/       # Six attack implementations
├── services/
│   ├── attacker/Dockerfile
│   └── rdp/README.md
├── src/
│   ├── qds/             # L1 — Teleportation-based QDS
│   ├── security/        # L3 — Identity, Auth, Nonce, Replay
│   ├── detection/       # L2 — Baseline, Statistics, Policy
│   ├── ledger/          # L4 — Hash-chain, Verifier
│   └── calibration/     # Offline calibration
├── experiments/         # Blind evaluation scripts
├── tests/               # Unit and integration tests
├── docs/                # Operations and architecture docs
├── docker-compose.yml
├── Makefile
└── requirements.txt
```

## Prerequisites

**Docker is required.**  See [docs/DOCKER_OPERATIONS.md](docs/DOCKER_OPERATIONS.md)
for installation instructions.

## Quick Start

```bash
# Build all containers
make build

# Start the isolated testbed
make up

# Run calibration (freezes thresholds)
make calibrate

# Access Judge Mode dashboard
open http://localhost:8501

# Run all attacks
make attack-all

# Run blind evaluation
make blind

# Stop
make down
```

## Attack Harness

Six distinct executable attacks, each implemented as a real adversarial
client against the API:

| Attack | Primary Layer | Expected |
|---|---|---|
| Forgery A (invalid signature) | L1 | REJECT |
| Forgery B (valid-path experiment) | L1/L2 | measured |
| Impersonation | L3 | REJECT |
| Replay | L3 | REJECT |
| Unauthorized Verification | L3 | REJECT |
| Channel Manipulation | L2 | QUARANTINE/REJECT |
| Ledger Tampering | L4 | Integrity violation |

See `make attack-all` or individual `make attack-*` commands.

## Documentation

| Document | Description |
|---|---|
| [DOCKER_OPERATIONS.md](docs/DOCKER_OPERATIONS.md) | Build, run, access, troubleshoot |
| [CONTAINER_ARCHITECTURE.md](docs/CONTAINER_ARCHITECTURE.md) | Container topology, networks, volumes |

## Important Limitations

- **Simulator:** Qiskit-Aer executes the quantum circuit computationally; it does not reproduce physical hardware noise.
- **Ledger:** The local hash-chain provides tamper evidence; it is **not** decentralized blockchain consensus.
- **No AI/ML:** The competition build contains no ML inference.
- **Empirical results:** Attack-detection metrics describe observed implementation behaviour under the tested threat model. They are not formal QDS security bounds.

## Docker Validation Status

> **Docker runtime validation was NOT performed** because Docker is not
> installed in the current development environment.  After Docker is installed,
> follow the verification steps in [DOCKER_OPERATIONS.md](docs/DOCKER_OPERATIONS.md).
