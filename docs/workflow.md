# Q-SENTINEL v9 Workflow

## Overview

Q-SENTINEL implements a quantum-inspired digital signature verification system.
The protocol uses simulated quantum key distribution (six-state QDS) to detect
forgery, replay, impersonation, and channel manipulation attacks.

## End-to-End Workflow

```
┌─────────────┐    Key Distribution     ┌─────────────┐
│             │  ─────────────────────►  │             │
│   ALICE     │                          │    BOB      │
│  (Signer)   │  ◄─────────────────────  │ (Verifier)  │
│             │    Verification Result   │             │
└─────────────┘                          └─────────────┘
       │                                        │
       │  k₀, k₁ ∈ {|0⟩,|1⟩,|+⟩,|−⟩,|i⟩,|−i⟩}  │
       │                                        │
       ▼                                        ▼
  ┌──────────┐                           ┌──────────┐
  │ KeyVault │                           │ Probes   │
  │ (L1)     │                           │ (L2/L3)  │
  └──────────┘                           └──────────┘
                                                │
                                                ▼
                                         ┌──────────┐
                                         │ Ledger   │
                                         │ (L4)     │
                                         └──────────┘
```

### Step 1: Key Distribution (Pre-signing)

Alice generates two sequences of quantum key elements (k₀ and k₁), each of
length L, from the six-state ensemble. These are stored in the **KeyVault**.

```python
from src.keyvault import global_keyvault
session = global_keyvault.create_session("alice", L=300)
```

### Step 2: Signing

To sign message bit `b`, Alice reveals the classical description of `k_b` to
Bob via the API. The KeyVault enforces single-use: once revealed, the session
cannot be used again.

### Step 3: Verification (Multi-Vector Detection)

Bob submits a verification request to the API endpoint `/v1/qds/verify`.
The request passes through four detection layers:

| Layer | Probe | What it checks |
|-------|-------|----------------|
| L3 | `AuthenticationProbe` | ML-DSA-65 signature, authorization |
| L3 | `FreshnessProbe` | Nonce uniqueness, timestamp validity |
| L1 | `TeleportationQDS` | Quantum teleportation circuit execution |
| L2 | `StatisticalProbe` | Mismatch rate against calibrated thresholds |

### Step 4: Correlation & Decision

The **CorrelationEngine** collects all findings and produces a final decision:

- **ACCEPT**: All probes pass (mismatch rate ≤ τ_low)
- **QUARANTINE**: τ_low < mismatch rate ≤ τ_high, or a non-critical finding
- **REJECT**: Any probe produces a REJECT-severity finding

### Step 5: Evidence Recording

Every verification event is recorded in the **Evidence Ledger**, an HMAC-SHA256
keyed hash chain stored in SQLite with `BEGIN IMMEDIATE` isolation.

## Running the System

### Track A (Native, No Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Provision credentials (alice, bob, charlie, mallory)
python attacker/provision.py

# Start the API server
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000

# Run integration tests
make test-local

# Run the multi-vector matrix experiment
python -m experiments.multi_vector_matrix

# Start the dashboard
streamlit run apps/dashboard/app.py
```

### Track B (Docker Compose)

```bash
make build
make up
make test
make blind
```

## Security Boundaries

See [SECURITY_ANALYSIS.md](SECURITY_ANALYSIS.md) for the formal adversary model
and probability bounds.

See [THREAT_MODEL.md](THREAT_MODEL.md) for the specific attack vectors tested.

See [LIMITATIONS.md](LIMITATIONS.md) for environmental constraints and what
the protocol does NOT claim.
