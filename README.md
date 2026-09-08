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

```bash
# Provision credentials (one-time)
set PYTHONPATH=. && python attacker/provision.py

# Start the API
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000

# Run tests
make test-local

# Start the dashboard
streamlit run apps/dashboard/app.py
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
│   │       ├── verify.py       # Core verification endpoint
│   │       ├── ledger.py       # Ledger audit endpoints
│   │       └── calibration.py  # Threshold calibration
│   └── dashboard/
│       └── app.py              # Streamlit judge mode dashboard
├── src/
│   ├── qds/
│   │   ├── key_material.py     # Six-state key element generation (CSPRNG)
│   │   ├── teleportation_qds.py # Teleportation circuit builder
│   │   ├── verification.py     # Mismatch rate computation
│   │   └── noise.py            # Depolarizing noise model
│   ├── keyvault/               # Single-use key distribution sessions
│   ├── detection/
│   │   ├── findings.py         # Finding dataclass (multi-vector)
│   │   ├── probes.py           # Independent detection probes
│   │   ├── correlation.py      # Correlation engine
│   │   ├── policy.py           # Threshold policy (fail-closed)
│   │   └── forgery_probability.py # Analytical bounds
│   ├── security/
│   │   ├── envelope.py         # ML-DSA-65 (FIPS 204) PQC
│   │   ├── identity.py         # PQC identity manager
│   │   ├── nonce.py            # SQLite nonce guard
│   │   └── rate_limit.py       # Token-bucket rate limiter
│   ├── ledger/
│   │   ├── hash_chain.py       # HMAC-SHA256 evidence ledger
│   │   └── verifier.py         # Chain integrity auditor
│   └── transport/
│       └── client.py           # HTTP transport abstraction
├── attacker/
│   ├── provision.py            # Credential generation (alice, bob, mallory)
│   ├── scenarios.py            # Attack scenario definitions
│   ├── runner.py               # Attack execution script
│   └── scenarios/
│       ├── timing_oracle.py    # Side-channel test
│       └── adaptive_x.py      # F3 regression test
├── experiments/
│   ├── blind_eval.py           # Blind evaluation (TP/TN/FP/FN)
│   ├── forgery_curve.py        # P_forge vs disturbance sweep
│   └── multi_vector_matrix.py  # Detection coverage matrix
├── tests/
│   ├── integration/            # FastAPI TestClient tests
│   └── property/               # Hypothesis property-based tests
├── docs/
│   ├── SECURITY_ANALYSIS.md    # Formal adversary model
│   ├── THREAT_MODEL.md         # Attack vector catalog
│   ├── LIMITATIONS.md          # Environmental constraints
│   └── workflow.md             # End-to-end workflow
└── data/
    └── calibration/
        └── thresholds.json     # Shipped calibration artifact
```

---

## Security Claims & Limitations

### What we claim

1. A six-state QDS protocol with P_forge ≤ 10⁻⁶ at L=300 against an
   individual-measurement adversary without quantum memory.
2. Multi-vector detection that catches forgery, replay, impersonation, and
   channel manipulation independently (no short-circuit).
3. Post-quantum request authentication via ML-DSA-65.
4. Tamper-evident evidence via HMAC-SHA256 hash chain.

### What we do NOT claim

1. This is **not** a production quantum network. It runs on Qiskit Aer (simulator).
2. We do **not** claim security against a coherent-attack adversary with quantum memory.
3. The `pqcrypto` library is a Python binding; the implementation has not been
   audited for side channels.
4. The HMAC key is stored in an environment variable, not an HSM.

See [docs/LIMITATIONS.md](docs/LIMITATIONS.md) for the full list.

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
