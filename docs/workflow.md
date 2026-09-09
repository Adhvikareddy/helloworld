# Q-SENTINEL: Jury Demonstration Workflow & Evaluation Guide

This guide details the exact live demonstration sequence for technical judges and reviewers.
Every step provides the precise terminal command to execute, what output appears on screen, the exact numbers to highlight, and the technical justification.

---

## Preparation (Pre-Demo Verification)

Ensure the development environment is active and dependencies are loaded:

```bash
# Verify the test suite passes (89 tests)
python -m pytest tests/ -q
```

Expected output:
```text
......................................................................................... [100%]
89 passed, 1 warning in 12.5s
```

---

## Demo Step 1: Legitimate Signing and Verification Flow

**Concept:** Alice pre-distributes quantum states to Bob and Charlie, reveals keys corresponding to message bit 0, and Bob verifies. Under honest channel noise (disturbance = 0.02), the legitimate signature is accepted.

### Command
```bash
python -c "
from fastapi.testclient import TestClient
from apps.api.main import app
from src.security.envelope import PQCEnvelope
from src.security.identity import global_pqc_identity
import time, uuid

client = TestClient(app)
alice_pk, alice_sk = PQCEnvelope.generate_keypair()
global_pqc_identity.register_participant('alice_demo', alice_pk, is_verifier=False, role='auditor')
global_pqc_identity.register_participant('bob_demo', alice_pk, is_verifier=True, role='verifier')

session_id = f'sess-demo-{uuid.uuid4()}'
# 1. Distribute
dist = {'session_id': session_id, 'signer_id': 'alice_demo', 'verifiers': ['bob_demo'], 'L': 60, 'nonce': f'n-d-{uuid.uuid4()}', 'timestamp': time.time()}
dist['signature'] = PQCEnvelope.sign_payload(alice_sk, dist)
r_dist = client.post('/v1/qds/distribute', json=dist).json()

# 2. Reveal
rev = {'session_id': session_id, 'signer_id': 'alice_demo', 'message_bit': 0, 'nonce': f'n-r-{uuid.uuid4()}', 'timestamp': time.time()}
rev['signature'] = PQCEnvelope.sign_payload(alice_sk, rev)
revealed = client.post('/v1/qds/reveal', json=rev).json()['revealed_keys']

# 3. Verify
ver = {'session_id': session_id, 'signer_id': 'alice_demo', 'verifier_id': 'bob_demo', 'nonce': f'n-v-{uuid.uuid4()}', 'timestamp': time.time(), 'message_bit': 0, 'revealed_keys': revealed}
ver['signature'] = PQCEnvelope.sign_payload(alice_sk, ver)
res = client.post('/v1/qds/verify', json=ver).json()
print('DECISION:', res['decision'])
print('MISMATCH RATE:', [f['metrics']['mismatch_rate'] for f in res['findings'] if f.get('detector') == 'QuantumDetector'][0])
print('THRESHOLD (tau_low):', [f['metrics']['tau_low'] for f in res['findings'] if f.get('detector') == 'QuantumDetector'][0])
"
```

### What Appears on Screen
```text
DECISION: ACCEPT
MISMATCH RATE: 0.0000  (or ~0.02 with channel noise)
THRESHOLD (tau_low): 0.1613
```

### What to Point At to the Jury
- Point to **DECISION: ACCEPT**.
- Highlight that **MISMATCH RATE $\le$ THRESHOLD ($\tau_{\text{low}}$)**.
- Note that unlike the v91 defect which rejected at channel noise > 0, the threshold is dynamically calibrated against honest channel noise ($e_{\text{honest}} \approx 0.02$), ensuring legitimate signatures accept reliably under real optical noise conditions.

---

## Demo Step 2: Adversarial Quantum Key Forgery Detection

**Concept:** Mallory attempts to forge Alice's signature by guessing key values at random without knowing Alice's states or Bob's secret measurement bases.

### Command
```bash
python -c "
from fastapi.testclient import TestClient
from apps.api.main import app
from src.security.envelope import PQCEnvelope
from src.security.identity import global_pqc_identity
import time, uuid, random

client = TestClient(app)
alice_pk, alice_sk = PQCEnvelope.generate_keypair()
global_pqc_identity.register_participant('alice_demo2', alice_pk, is_verifier=False, role='auditor')
global_pqc_identity.register_participant('bob_demo2', alice_pk, is_verifier=True, role='verifier')

session_id = f'sess-demo2-{uuid.uuid4()}'
dist = {'session_id': session_id, 'signer_id': 'alice_demo2', 'verifiers': ['bob_demo2'], 'L': 60, 'nonce': f'n-d-{uuid.uuid4()}', 'timestamp': time.time()}
dist['signature'] = PQCEnvelope.sign_payload(alice_sk, dist)
client.post('/v1/qds/distribute', json=dist)

# Mallory guesses random quantum bases and bits
forged_keys = [{'bit_index': i, 'basis': random.choice(['X', 'Y', 'Z']), 'bit_value': random.choice([0, 1])} for i in range(60)]

ver = {'session_id': session_id, 'signer_id': 'alice_demo2', 'verifier_id': 'bob_demo2', 'nonce': f'n-v-{uuid.uuid4()}', 'timestamp': time.time(), 'message_bit': 0, 'revealed_keys': forged_keys}
ver['signature'] = PQCEnvelope.sign_payload(alice_sk, ver)
res = client.post('/v1/qds/verify', json=ver).json()
print('DECISION:', res['decision'])
print('MISMATCH RATE:', [f['metrics']['mismatch_rate'] for f in res['findings'] if f.get('detector') == 'QuantumDetector'][0])
print('THRESHOLD (tau_high):', [f['metrics']['tau_high'] for f in res['findings'] if f.get('detector') == 'QuantumDetector'][0])
"
```

### What Appears on Screen
```text
DECISION: REJECT
MISMATCH RATE: 0.4500  (elevated around 50%)
THRESHOLD (tau_high): 0.1935
```

### What to Point At to the Jury
- Point to **DECISION: REJECT**.
- Highlight that the adversary incurs a **$\approx 50\%$ mismatch rate** on the matched basis subset because non-orthogonal quantum states cannot be cloned or guessed without errors (Helstrom bound limit: $p_{\text{err}} \ge 21.13\%$).
- The mismatch rate substantially exceeds $\tau_{\text{high}}$ (0.19), triggering an immediate, unambiguous REJECT verdict.

---

## Demo Step 3: Signature Transferability (Why QDS is a Signature, Not a MAC)

**Concept:** In a MAC, a verifier (Bob) can forge signatures against other parties. In Q-SENTINEL, Bob fabricates a signature claiming his own recorded measurement outcomes. When Bob checks his own fabrication, it matches his records perfectly (ACCEPT). However, when the exact same fabrication is submitted to Charlie, Charlie **REJECTS**.

### Command
```bash
python -m attacker.runner --attack forgery_by_verifier
```

### What Appears on Screen
```text
--- Scenario: Forgery by Verifier (Transferability) ---
verifier=bob -> ACCEPT
verifier=charlie -> REJECT
```

### What to Point At to the Jury
- Point directly to the contrasting lines:
  - **verifier=bob $\to$ ACCEPT**
  - **verifier=charlie $\to$ REJECT**
- Explain to the jury: *"Bob knows his own measurement records, so he can fabricate a key that matches himself perfectly. But Bob has zero knowledge of Charlie's independent measurement bases. When Charlie evaluates Bob's fabrication, Charlie sees a mismatch rate near 50%, rejecting the forgery. This mathematically proves transferability and non-repudiation."*

---

## Demo Step 4: Coherent Channel Attack Detection ($R_x$ Rotation)

**Concept:** In v8, a fixed $|+\rangle$ state allowed an adversary to perform pure X-axis channel rotations ($R_x(\pi)$) with a deviation of only `0.00006`, making channel eavesdropping invisible. Q-SENTINEL's six-state ensemble and tomography probe completely eliminate this blind spot.

### Command
```bash
python -m experiments.adaptive_x
```

### What Appears on Screen
```text
angle_pi=0.25: m_hat=0.1093, decision=QUARANTINE
angle_pi=0.50: m_hat=0.3716, decision=REJECT
angle_pi=0.75: m_hat=0.5526, decision=REJECT
angle_pi=1.00: m_hat=0.6791, decision=REJECT
Wrote 4 rows to experiments/results/adaptive_x.csv
```

### What to Point At to the Jury
- Point to the angle $\theta = 1.00\pi$ row: **m_hat = 0.6791, decision = REJECT**.
- Contrast this with the old v8 figure:
  - **v8 Fixed State Deviation:** `0.00006` (completely invisible, indistinguishable from clean channel).
  - **Q-SENTINEL Six-State Mismatch:** `0.6791` (overwhelming detection, 10,000x greater signal-to-noise ratio).
- Reference the generated dataset: `experiments/results/adaptive_x.csv`.

---

## Demo Step 5: Forgery Probability Scaling ($P_{\text{forge}}$ Curve)

**Concept:** Demonstrate that the adversary's probability of undetected forgery decays exponentially with sequence length $L$.

### Command
```bash
python -c "
import csv
with open('experiments/results/forgery_curve.csv') as f:
    r = list(csv.DictReader(f))
print('L       | Disturbance | Emp Mismatch | Theoretical P_forge')
print('--------|-------------|--------------|--------------------')
for row in r[::3]:
    print(f\"{row['L']:<7} | {row['disturbance']:<11} | {row['emp_mismatch']:<12} | {row['P_forge_bound']}\")
"
```

### What Appears on Screen
```text
L       | Disturbance | Emp Mismatch | Theoretical P_forge
--------|-------------|--------------|--------------------
300     | 0.000       | 0.0000       | 1.25e-07
300     | 0.150       | 0.1042       | 3.89e-06
300     | 0.300       | 0.1985       | 1.000000
```

### What to Point At to the Jury
- Show that at key length $L = 300$, under legitimate channel noise, the theoretical upper bound on forgery probability is:
  $$P_{\text{forge}} < 10^{-6}$$
- Cite `experiments/results/forgery_curve.csv`.

---

## Demo Step 6: Immutable Ledger Tamper Localization

**Concept:** An adversary gains direct database access and attempts to alter a verification verdict from REJECT to ACCEPT. The cryptographic hash chain instantly detects and localizes the exact row of tampering.

### Command
```bash
python -c "
from src.ledger.hash_chain import EvidenceLedger
from src.ledger.verifier import verify_ledger
import sqlite3, time

db = 'data/demo_tamper.db'
ledger = EvidenceLedger(db_path=db)
for i in range(5):
    ledger.record_event({'session_id': f's-{i}', 'signer_id': 'alice', 'verifier_id': 'bob', 'decision': 'REJECT', 'findings': []})

print('Before Tampering: verify_ledger ->', verify_ledger(db_path=db))

# Adversary tampers with row 3
with sqlite3.connect(db) as conn:
    conn.execute(\"UPDATE evidence SET decision = 'ACCEPT' WHERE seq_num = 3\")
    conn.commit()

print('After Tampering:  verify_ledger ->', verify_ledger(db_path=db))
import os; os.remove(db)
"
```

### What Appears on Screen
```text
Before Tampering: verify_ledger -> True
Hash mismatch at seq_num 3. Data tampered.
After Tampering:  verify_ledger -> False
```

### What to Point At to the Jury
- Point to: **`Hash mismatch at seq_num 3. Data tampered.`**
- Point to: **`After Tampering: verify_ledger -> False`**.
- Explain that each record incorporates the HMAC-SHA256 signature and previous record's hash. Tampering with any row breaks the cryptographic chain forward to the tip.

---

## Jury FAQ: "Why Not Just Use Post-Quantum Classical Signatures and Skip the Quantum Part?"

### Prepared Technical Response for the Team:

> *"That is the critical architectural question. Post-quantum classical signatures (like ML-DSA-65 / Dilithium) rely on computational hardness assumptions — specifically the Short Integer Solution (SIS) problem over module lattices. While secure against Shor's and Grover's algorithms today, computational schemes remain vulnerable to future mathematical breakthroughs or unexpected lattice reduction algorithms.*
>
> *Quantum Digital Signatures provide **physical, information-theoretic unforgeability** grounded in the laws of quantum mechanics (the No-Cloning Theorem and Helstrom's discrimination bound). Even an adversary with infinite classical and quantum computing power cannot clone non-orthogonal quantum states or eavesdrop on the channel without inducing detectable disturbance.*
>
> *Furthermore, classical signatures cannot detect eavesdropping during key distribution. Q-SENTINEL uses a hybrid architecture: ML-DSA-65 provides post-quantum identity authentication on classical network packets, while QDS ensures that the signature validity itself is guaranteed by the physics of the universe. It is defense-in-depth across both computational and physical cryptographic layers."*
