# Q-SENTINEL v9

**Quantum-Inspired Cyber Threat Detection for Digital Signature Security**

> Smart India Hackathon 2026 · PS SIH26141 · Egreen Quanta · Blockchain & Cybersecurity

---

## What is Q-SENTINEL?

Q-SENTINEL is a quantum-inspired digital signature verification system that uses
simulated six-state quantum key distribution (QDS) to detect **forgery, replay,
impersonation, and channel manipulation** attacks against digital signatures.

It is **not** an AI/ML system. It uses physics-based detection: the information-disturbance
tradeoff of quantum mechanics makes forging a signature statistically detectable.

### Key Properties

| Property | How |
|----------|-----|
| **Forgery detection** | Six-state QDS with P_forge ≈ 10⁻⁶ at L=300 |
| **Replay prevention** | SQLite-persisted nonce guard + session single-use |
| **Post-quantum auth** | ML-DSA-65 (FIPS 204) for request signing |
| **Tamper-evident log** | HMAC-SHA256 hash chain with `BEGIN IMMEDIATE` atomicity |
| **Multi-vector detection** | Independent probes + correlation engine (not single-path) |
| **Fail-closed** | 503 if calibration artifact is missing |
| **Side-channel protected** | Constant-time response envelope + response tiering |

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                   FastAPI Server                      │
│                                                       │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌────────┐ │
│  │ L3 Auth │→ │ L1 QDS  │→ │L2 Stats  │→ │L4 Log  │ │
│  │ Probes  │  │ Core    │  │ Probes   │  │ Ledger │ │
│  └─────────┘  └─────────┘  └──────────┘  └────────┘ │
│       ↓            ↓            ↓            ↓       │
│  ┌──────────────────────────────────────────────────┐ │
│  │           Correlation Engine                     │ │
│  │     ACCEPT / QUARANTINE / REJECT                 │ │
│  └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### Detection Layers

- **L1 (Quantum Core)**: Teleportation-based QDS using Qiskit Aer with six-state ensemble
- **L2 (Statistical)**: Binomial mismatch rate test with family-wise error control (scipy.stats)
- **L3 (Security)**: ML-DSA-65 authentication, nonce freshness, timestamp validity, rate limiting
- **L4 (Evidence)**: HMAC-SHA256 hash chain with monotonic sequence numbers, audit replay

---

## Quick Start

### Prerequisites

- Python 3.11+ (development uses 3.14, Docker uses 3.11)
- pip

### Installation

```bash
git clone <repo>
cd helloworld
pip install -r requirements.txt
```

### Run

#### Option A: One-Click Startup (Backend + Frontend)
```bash
# Windows Batch
start.bat

# PowerShell
./start.ps1
```

#### Option B: Manual Startup
```bash
# 1. Provision credentials (one-time setup)
python attacker/provision.py

# 2. Start FastAPI Backend (includes automatic startup calibration)
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000

# 3. Start React Frontend Dashboard (in a second terminal)
cd frontend
npm install
npm run dev
# Open http://localhost:3000 in your browser
```

#### Option C: Verification & Smoke Tests
```bash
# Full pytest suite (89/89 tests)
python -m pytest tests/ -q

# Run full evaluation suite generating all 9 evidence CSVs
make evaluate

# CLI Adversarial Attack Suite
python -m attacker.runner
```

### Docker

```bash
make build
make up
make demo
```

---

## Project Structure

```
.
├── apps/
│   ├── api/                    # FastAPI verification server
│   │   ├── main.py
│   │   └── routes/
│   │       ├── verify.py       # Core verification endpoint (constant-time, role-tiered)
│   │       ├── ledger.py       # Ledger audit endpoints
│   │       ├── testbed.py      # Operator-authenticated channel control
│   │       └── calibration.py  # Measured baseline threshold calibration
│   └── dashboard/
│       └── app.py              # Streamlit judge mode dashboard
├── src/
│   ├── qds/
│   │   ├── key_material.py     # Six-state key element generation (CSPRNG)
│   │   ├── teleportation_qds.py # Teleportation circuit builder (coherent Rx/Rz rotations)
│   │   ├── verification.py     # Mismatch rate computation
│   │   └── noise.py            # Depolarizing and rotational noise models
│   ├── keyvault/               # Single-use key distribution sessions
│   ├── detection/
│   │   ├── findings.py         # Finding dataclass (multi-vector)
│   │   ├── probes.py           # Independent detection probes (Auth, Freshness, Stats, Tomography)
│   │   ├── correlation.py      # Correlation engine
│   │   ├── policy.py           # Threshold policy (derived from measured baseline, fail-closed)
│   │   └── forgery_probability.py # Analytical bounds
│   ├── security/
│   │   ├── envelope.py         # ML-DSA-65 (FIPS 204) PQC
│   │   ├── identity.py         # PQC identity manager (with registered roles)
│   │   ├── nonce.py            # SQLite nonce guard
│   │   └── rate_limit.py       # Token-bucket rate limiter
│   ├── ledger/
│   │   ├── hash_chain.py       # HMAC-SHA256 evidence ledger (BEGIN IMMEDIATE concurrency, checkpoints)
│   │   └── verifier.py         # Chain integrity auditor and checkpoint verifier
│   └── transport/
│       └── client.py           # HTTP transport abstraction
├── attacker/
│   ├── provision.py            # Credential generation (alice, bob, charlie, mallory)
│   ├── runner.py               # Attack execution script (--attack flag)
│   └── scenarios/
│       ├── forgery_by_verifier.py # Transferability forgery scenario
│       └── adaptive_x.py      # Coherent rotation scenario
├── experiments/
│   ├── noise_sweep.py          # Honest channel baseline measurement
│   ├── adaptive_x.py           # Coherent X-rotation evaluation
│   ├── blind_eval.py           # Blind evaluation (Threat = Positive Class)
│   ├── roc_curve.py            # ROC curve and AUC evaluation
│   ├── concurrent_campaign.py  # Concurrency throughput and integrity benchmark
│   ├── latency_split.py        # Constant-time latency split evaluation
│   ├── forgery_curve.py        # P_forge vs key length / disturbance
│   ├── multi_vector_matrix.py  # Multi-vector threat detection matrix
│   └── results/                # Generated evidence CSV files (9 datasets)
├── tests/
│   ├── integration/            # FastAPI integration tests (16 tests)
│   ├── unit/                   # Unit, compliance, and ledger tests
│   └── property/               # Hypothesis property-based tests
└── docs/
    ├── SECURITY_ANALYSIS.md    # Formal adversary model & who-knows-what-when matrix
    ├── DELIVERABLES.md         # SIH PS26141 expected deliverables mapping table
    ├── LIMITATIONS.md          # Protocol & environment constraints
    └── workflow.md             # Step-by-step jury demonstration guide
```

---

## Security Claims & Limitations

### What we claim

1. A six-state QDS protocol with $P_{\text{forge}} \le 10^{-6}$ at $L=300$ against an
   individual-measurement adversary without quantum memory (evaluated in `experiments/results/forgery_curve.csv`).
2. Multi-vector detection that catches forgery, replay, impersonation, and
   channel manipulation independently (evaluated in `experiments/results/multi_vector_matrix.csv`).
3. Post-quantum request authentication via ML-DSA-65 (FIPS 204).
4. Tamper-evident evidence via HMAC-SHA256 hash chain with checkpoint verification.
5. True signature transferability: Bob's fabrication against Charlie is rejected (`experiments/results/multi_vector_matrix.csv`).

### What we do NOT claim

1. This is **not** a production physical optical quantum network. It executes on IBM Qiskit Aer quantum circuit simulation.
2. We do **not** claim security against a coherent-attack adversary with quantum memory.
3. The construction currently signs **one bit ($m \in \{0, 1\}$) per session**, not arbitrary-length messages directly (see [docs/LIMITATIONS.md](docs/LIMITATIONS.md)).
4. The HMAC key is stored in an environment variable, not a hardware security module (HSM).
5. The Google Drive folder linked in PS26141 (`https://drive.google.com/drive/folders/1rgGdaPn9rdGZfkaqc3MKVfdCK8r5X_gk`) is an unauthenticated SPA drive shell without direct programmatic data access, documented as an open risk in [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

See [docs/LIMITATIONS.md](docs/LIMITATIONS.md) for the complete specification of limitations and constraints.

---

## Testing

```bash
# All tests
make test-local

# Integration only
make test-integration

# Property-based
make test-property

# Multi-vector detection matrix
python -m experiments.multi_vector_matrix

# Forgery curve
python -m experiments.forgery_curve

# Blind evaluation (requires running API)
python -m experiments.blind_eval
```

---

## License

Academic project for SIH 2026.
