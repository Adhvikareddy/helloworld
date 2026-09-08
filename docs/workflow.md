# Q-SENTINEL Judge Demonstration Workflow

> **Version:** v8 · **Competition:** SIH 2026 · **PS:** PS26141 · **Team:** Egreen Quanta  
> **Theme:** Blockchain & Cybersecurity

---

## 1. What Q-SENTINEL Is

Q-SENTINEL is a software prototype that detects threats in **quantum digital signature (QDS) verification** by observing how quantum measurement statistics change under adversarial conditions.

Instead of relying on a single pass/fail signature check, Q-SENTINEL **repeats quantum measurements many times** and asks: *"Does the resulting pattern still look like a legitimate verification?"*

If the pattern deviates significantly from the expected baseline, Q-SENTINEL flags the request as suspicious — even when the classical request appears valid.

**What it is:** A quantum-inspired threat detection testbed built with Qiskit-Aer simulation.  
**What it is not:** A production cryptographic system, an AI/ML model, or a decentralized blockchain.

---

## 2. The Problem

When a quantum digital signature is verified, the verification process involves quantum measurement. In theory, an adversary who:

- **Forges** a signature
- **Replays** an old valid signature
- **Impersonates** a different signer
- **Manipulates** the quantum communication channel

…should cause detectable changes in the measurement pattern.

**Q-SENTINEL's job** is to demonstrate that these statistical changes can be detected programmatically, using a testbed that executes real quantum circuits on a simulator.

---

## 3. Quantum Concepts the Judge Needs

### Qubit
A qubit is the smallest unit of quantum information. Unlike a classical bit (0 or 1), a qubit can be in a **combination of both states simultaneously** — called a superposition. When you measure it, you get either 0 or 1, with probabilities determined by the superposition.

*Analogy: Think of a spinning coin. While spinning, it's "both heads and tails." When it lands, you see one outcome — but the probability of each side depends on how it was flipped.*

### Quantum State
A quantum state describes the complete information about a qubit (or multiple qubits). It determines the probabilities of each measurement outcome.

### Bell State
A Bell state is a specific two-qubit state where the qubits are **maximally correlated** — measuring one instantly determines what the other will be, regardless of distance. This is called **entanglement**.

*Analogy: Imagine two sealed envelopes, each containing a card. One always has "red" and the other always has "blue." You don't know which is which until you open one — but the moment you open yours and see "red," you instantly know the other is "blue."*

### Teleportation
Quantum teleportation transfers a quantum state from one qubit to another using an entangled Bell pair and two classical bits of information. **No physical object is transported** — the state (information) is transferred.

*Analogy: Think of teleportation as faxing — the original document's information is transferred to a new sheet at the receiver, and you need a phone call (classical bits) to tell the receiver how to reconstruct it.*

### Measurement
When you measure a qubit, the superposition collapses to a definite outcome (0 or 1). The outcome is probabilistic — you cannot predict it with certainty, only its probability.

We measure in three different **bases** (X, Y, Z) — each reveals different information about the state:
- **Z-basis:** Standard measurement (computational basis)
- **X-basis:** Measures superposition phase (apply Hadamard first)
- **Y-basis:** Measures circular phase (apply S†, then Hadamard first)

### Repeated Shots
Since each measurement gives a random outcome, we repeat the experiment many times (e.g., 1024 shots) and study the **distribution** of outcomes. The distribution tells us whether the quantum state is behaving as expected.

*Analogy: Flipping a fair coin once tells you almost nothing. Flipping it 1000 times and getting 950 heads tells you something is wrong with the coin.*

---

## 4. What We Actually Built

### Technology Stack
| Component | Technology | Purpose |
|---|---|---|
| Quantum simulation | **Qiskit-Aer** (statevector simulator) | Execute quantum circuits computationally |
| API | **FastAPI** (Python) | Host the 4-layer verification pipeline |
| Dashboard | **Streamlit** | Judge-facing interactive UI |
| Evidence | **SQLite** + SHA-256 hash chain | Tamper-evident event ledger |
| Testbed | **Docker Compose** | One-command reproducible environment |
| Attack harness | **Python + requests** | Real adversarial HTTP client |

### Four Runtime Layers
1. **L3 — Security Guard:** Checks identity, authorization, nonce freshness, timestamp validity. Rejects unauthorized/replayed requests BEFORE any quantum execution.
2. **L1 — QDS Verification Core:** Constructs a teleportation circuit, executes it on Qiskit-Aer, measures in X/Y/Z bases with configurable shots.
3. **L2 — Statistical Threat Detector:** Compares observed measurement probabilities against a calibrated legitimate baseline using deviation D and chi-square statistics.
4. **L4 — Evidence Ledger:** Records every decision in a SHA-256 hash-chained SQLite ledger for tamper-evident audit.

### Simulator Limitations
> **Important:** Qiskit-Aer simulates quantum circuits on a classical computer. It does **not** use real quantum hardware. The simulator produces exact probability distributions (modulo finite shot noise) — it does not model physical hardware noise, decoherence, or real quantum channel attacks.
> 
> This means our "channel manipulation" is a controlled parameter injected into the circuit, not an external attacker physically interfering with a quantum channel. We clearly label this as a **controlled channel-disturbance experiment**.

---

## 5. Architecture

```
UNTRUSTED REQUEST
       ↓
  L3 — Security & Authorization Guard
  │    ├─ Is the timestamp fresh?
  │    ├─ Has this nonce been used before?
  │    ├─ Is the signer registered?
  │    └─ Is the verifier authorized?
  │    (REJECT here → no quantum execution wasted)
       ↓  (authorized + fresh)
  L1 — QDS Verification Core  (Qiskit-Aer)
  │    ├─ Prepare message state |+⟩
  │    ├─ Prepare Bell pair
  │    ├─ Bell-basis measurement
  │    ├─ Pauli correction (X/Z conditioned on classical bits)
  │    └─ Projective measurement in X, Y, Z bases
       ↓  (measurement probabilities)
  L2 — Statistical Threat Detector
  │    ├─ Compare observed P(X/Y/Z) against calibrated baseline
  │    ├─ Compute deviation D (weighted squared distance)
  │    ├─ Compute chi-square cross-check
  │    └─ Apply frozen threshold policy
       ↓
  ACCEPT / QUARANTINE / REJECT
       ↓
  L4 — Tamper-Evident Evidence Ledger
       ├─ Serialize event canonically
       ├─ Link to previous hash
       └─ SHA-256(previous_hash + canonical_event) → store
```

**Why the order matters:**
- L3 first: Don't waste expensive quantum computation on unauthorized requests
- L1 before L2: Statistics require actual measurements
- L4 last: Every decision is immutably recorded, including rejections

---

## 6. End-to-End Legitimate Request

**What happens when a legitimate signer sends a valid verification request:**

1. **Client** sends POST to `/v1/qds/verify` with:
   - `signer_id: "alice"`, `verifier_id: "bob"`
   - Fresh `nonce`, current `timestamp`
   - `shots: 1024`, `signature`, `message_digest`

2. **L3** checks:
   - ✅ Timestamp is within 300 seconds
   - ✅ Nonce has never been seen before (stored in set)
   - ✅ `"alice"` is in the registered signers allowlist
   - ✅ `"bob"` is in the authorized verifiers allowlist

3. **L1** executes three Qiskit circuits (one per basis: X, Y, Z):
   - **State prep:** Apply H to qubit 0 → creates |+⟩
   - **Bell pair:** Apply H to qubit 1, then CNOT(1→2) → creates Bell state
   - **Bell measurement:** CNOT(0→1), H(0), measure qubits 0 and 1
   - **Pauli correction:** Apply X to qubit 2 if classical bit 1 = 1; apply Z if classical bit 0 = 1
   - **Projective measurement:**
     - X-basis: H then measure qubit 2
     - Y-basis: S†, H, then measure qubit 2
     - Z-basis: measure qubit 2 directly
   - Run each circuit for 1024 shots
   - Extract P(0) and P(1) from the teleported qubit's measurement

4. **Expected results for |+⟩ state (no disturbance):**
   - X: P(0) ≈ 1.0, P(1) ≈ 0.0 (deterministic — |+⟩ is X eigenstate)
   - Y: P(0) ≈ 0.5, P(1) ≈ 0.5 (uniform — |+⟩ is unbiased in Y)
   - Z: P(0) ≈ 0.5, P(1) ≈ 0.5 (uniform — |+⟩ is unbiased in Z)

5. **L2** compares observed probabilities against calibrated baseline:
   - Computes deviation: `D = Σ w·(p_observed - p_baseline)²`
   - Computes chi-square: `χ² = Σ N·(p_observed - p_baseline)²/p_baseline`
   - Applies thresholds: `D ≤ τ_low → ACCEPT`

6. **L4** records the event:
   - Creates canonical JSON of all event fields
   - Retrieves previous hash from the last ledger entry
   - Computes `SHA-256(previous_hash + canonical_event)`
   - Stores the event with both hashes

7. **Response** returned with `decision: "ACCEPT"`, deviation score, chi-square, evidence_id, calibration status.

---

## 7. Judge Demo — EXACT LIVE SEQUENCE

> **Prerequisites:** Docker containers running (`make build && make up`), calibration done (`make calibrate`).

### STEP 1 — Show Dashboard
Open `http://localhost:8501` in the browser.

**What to say:** *"This is our Judge Mode dashboard. Every button executes a real attack against our live API — there are no pre-recorded results."*

Point out the calibration status indicator at the top.

### STEP 2 — Run Legitimate Request
Click **✅ LEGITIMATE**.

**What the judge sees:** Green "ACCEPT" badge, D ≈ 0 (very small), evidence_id, calibration status.

**What to say:** *"This is a legitimate verification. The quantum circuit ran 1024 times in three measurement bases. The observed distribution matches our calibrated baseline, so the system accepts it."*

### STEP 3 — Explain Why It Is Accepted
Point to the deviation score (D ≈ 0.001 or similar very small value).

**What to say:** *"D measures how far the measurement pattern deviates from what we expect for a legitimate request. A small D means the pattern is consistent with normal behavior."*

### STEP 4 — Run Replay Attack
Click **🔁 REPLAY**.

**What the judge sees:** Red "REJECT" badge, reason: "Replay detected".

**What to say:** *"We first sent a legitimate request (which succeeded), then resent the identical request with the same nonce. L3 caught the reused nonce and rejected it before any quantum computation occurred — saving resources."*

### STEP 5 — Explain L3 Rejection
**What to say:** *"L3 is the security guard layer. It checks four things: timestamp freshness, nonce uniqueness, signer identity, and verifier authorization. If any check fails, the request is rejected immediately, and the rejection is recorded in the evidence ledger."*

### STEP 6 — Run Impersonation Attack
Click **🎭 IMPERSONATION**.

**What the judge sees:** Red "REJECT" badge, reason: "Invalid identity binding".

**What to say:** *"The attacker submitted a request with a signer identity that isn't registered in our system. L3 uses an allowlist — only known, registered signers are accepted."*

### STEP 7 — Run Unauthorized Verifier
Click **🚫 UNAUTHORIZED**.

**What the judge sees:** Red "REJECT" badge, reason: "Unauthorized verifier".

**What to say:** *"Same concept, but for the verifier side. The verifier identity isn't in our authorized set."*

### STEP 8 — Run Channel Manipulation
Click **📡 CHANNEL**.

**What the judge sees:** Three results (low/medium/high disturbance). Low may ACCEPT or QUARANTINE; medium likely QUARANTINE; high likely REJECT.

**What to say:** *"This is our most important quantum experiment. We inject controlled noise into the quantum channel before measurement — simulating an attacker degrading the channel. At low disturbance, the pattern barely changes. At high disturbance, the deviation D becomes large enough to trigger REJECT. The quantum circuit runs fresh for each test."*

### STEP 9 — Run Forgery Attack
Click **🔴 FORGERY**.

**What the judge sees:** Red "REJECT" badge, reason: "invalid_qds_signature".

**What to say:** *"The attacker tampered with the message after signing. L1 detects that the signature is no longer valid and rejects without running the statistical detector."*

**Honest caveat if asked:** *"In our testbed, signature validity is signaled by a flag rather than full cryptographic verification. Implementing a complete QDS signature scheme is outside the scope of this prototype, but the detection pipeline and evidence recording are real."*

### STEP 10 — Tamper with Ledger
Click **🔗 TAMPER LEDGER**.

**What the judge sees:** "integrity_violation" with details about which field was modified.

**What to say:** *"We first created a legitimate event, then directly modified the database — changing the decision field. When we verify the hash chain, the SHA-256 fingerprint of the tampered record no longer matches, exposing the modification."*

### STEP 11 — Verify Ledger Integrity
Click **🔍 VERIFY FULL LEDGER CHAIN**.

**What the judge sees:** Either "INTEGRITY VIOLATION" (if ledger was tampered) or "Chain intact" (if clean).

**What to say:** *"Every event is linked to the previous one via SHA-256 hashing. Changing any field in any record breaks the chain. This is tamper-evident logging, not decentralized blockchain consensus."*

### STEP 12 — Show Final Evidence
Expand the "Full JSON" section of any result.

**What to say:** *"Every number in this JSON came from an actual system response — the deviation score from Qiskit measurements, the decision from our threshold policy, the evidence_id from the hash-chain ledger. Nothing is fabricated."*

---

## 8. Attack-by-Attack Technical Explanation

### Replay Attack
| Item | Detail |
|---|---|
| **Attacker action** | Capture a valid request and resubmit with identical nonce and session |
| **Request mutation** | None — exact copy of a previously accepted request |
| **Layer targeted** | L3 (nonce freshness guard) |
| **Does Qiskit execute?** | No — rejected before L1 |
| **Does L2 execute?** | No |
| **Expected result** | HTTP 403, REJECT |
| **Evidence generated** | L3 rejection event in ledger |
| **What the judge should understand** | Classical nonce-based replay protection works correctly |
| **What we must NOT claim** | This is not quantum replay protection — it is classical nonce freshness |

### Impersonation Attack
| Item | Detail |
|---|---|
| **Attacker action** | Submit request with unregistered signer_id |
| **Request mutation** | `signer_id` changed to adversarial identity |
| **Layer targeted** | L3 (identity binding guard) |
| **Does Qiskit execute?** | No — rejected before L1 |
| **Does L2 execute?** | No |
| **Expected result** | HTTP 403, REJECT |
| **Evidence generated** | L3 rejection event in ledger |
| **What the judge should understand** | Allowlist-based identity verification rejects all unknown signers |
| **What we must NOT claim** | This is not cryptographic certificate binding — it is a testbed allowlist |

### Unauthorized Verifier
| Item | Detail |
|---|---|
| **Attacker action** | Submit request with unregistered verifier_id |
| **Request mutation** | `verifier_id` changed to unauthorized identity |
| **Layer targeted** | L3 (authorization guard) |
| **Does Qiskit execute?** | No — rejected before L1 |
| **Does L2 execute?** | No |
| **Expected result** | HTTP 403, REJECT |
| **Evidence generated** | L3 rejection event in ledger |
| **What the judge should understand** | Allowlist-based authorization rejects all unregistered verifiers |
| **What we must NOT claim** | This is not RBAC or certificate-based authorization |

### Forgery A (Invalid Signature)
| Item | Detail |
|---|---|
| **Attacker action** | Tamper with message digest after signing |
| **Request mutation** | `message_digest` mutated, `is_invalid_signature=True` |
| **Layer targeted** | L1 (QDS validity) |
| **Does Qiskit execute?** | No — short-circuited by signature validity check |
| **Does L2 execute?** | No |
| **Expected result** | HTTP 200, decision=REJECT, reason=invalid_qds_signature |
| **Evidence generated** | L1 rejection event in ledger |
| **What the judge should understand** | The system detects and rejects invalid signatures |
| **What we must NOT claim** | This is NOT real cryptographic signature verification — see Section 9 |

### Forgery B (Valid-Path Experiment)
| Item | Detail |
|---|---|
| **Attacker action** | Submit valid request with channel disturbance |
| **Request mutation** | `disturbance_prob` set to tested level |
| **Layer targeted** | L1/L2 (quantum execution + statistical detection) |
| **Does Qiskit execute?** | **Yes** — full 3-basis circuit |
| **Does L2 execute?** | **Yes** — D and chi-square computed |
| **Expected result** | Depends on disturbance level |
| **Evidence generated** | Full detection event in ledger |
| **What the judge should understand** | Even valid-seeming requests can be detected statistically |
| **What we must NOT claim** | P_forge_emp is an empirical metric, NOT a formal security bound |

### Channel Manipulation
| Item | Detail |
|---|---|
| **Attacker action** | Specify disturbance parameter (low/medium/high) |
| **Request mutation** | `disturbance_prob` set to 0.10/0.25/0.50 |
| **Layer targeted** | L2 (statistical detector) |
| **Does Qiskit execute?** | **Yes** — rx/rz rotations injected into circuit before measurement |
| **Does L2 execute?** | **Yes** — D and chi-square computed from actual measurements |
| **Expected result** | ACCEPT/QUARANTINE/REJECT depending on level |
| **Evidence generated** | Full detection event with D, chi-square, thresholds |
| **What the judge should understand** | Increasing channel noise shifts the measurement distribution |
| **What we must NOT claim** | This is a CONTROLLED EXPERIMENT, not external quantum channel interception |

### Ledger Tampering
| Item | Detail |
|---|---|
| **Attacker action** | Directly modify SQLite database field |
| **Request mutation** | Database UPDATE (not API request) |
| **Layer targeted** | L4 (hash chain integrity) |
| **Does Qiskit execute?** | Only for setup (creating initial event) |
| **Does L2 execute?** | Only for setup |
| **Expected result** | Hash chain verification detects tampering |
| **Evidence generated** | Chain verification result |
| **What the judge should understand** | The hash chain makes any modification detectable |
| **What we must NOT claim** | This is local tamper evidence, not distributed consensus |

---

## 9. Forgery A vs Forgery B

This distinction is critical for honest evaluation.

### Forgery A — Invalid-Signature Mutation
The attacker modifies the message **after** signing. In a real QDS system, the signature would be cryptographically tied to the message, so modification would invalidate the signature.

**In our testbed:** We signal this with `is_invalid_signature=True`. The backend treats this flag as "the signature does not match the message" and rejects immediately **without** running the quantum circuit.

> ⚠️ **Honest limitation:** This is a **testbed shortcut**. We do not implement full cryptographic QDS signature verification. The `is_invalid_signature` flag is trusted — a real implementation would compute signature validity from the message and key.

### Forgery B — Valid-Path Adversarial Experiment
The attacker submits a request that **passes L1 validity** (the signature appears valid) but introduces channel disturbance. The full L1→L2 pipeline executes:
- Qiskit circuit runs with the disturbance
- Measurement distributions change
- D and chi-square increase
- The detection threshold determines ACCEPT/QUARANTINE/REJECT

This is a genuinely useful experiment: it measures the **empirical forgery-acceptance probability** (P_forge_emp) — how often an attacker with channel access can fool the detector.

> **What P_forge_emp is:** An empirical metric showing how the detector performs under the tested conditions.
> **What P_forge_emp is NOT:** A formal QDS forgery-security bound, an information-theoretic guarantee, or a proof of protocol security.

---

## 10. What the Logs Actually Mean

Every log field has a specific provenance:

| Field | Origin | Source |
|---|---|---|
| `attack_type` | Attacker script | Set by the scenario code |
| `actual_outcome` | API response | Extracted from `response.decision` |
| `deviation_score` | Qiskit + L2 | Computed from actual circuit measurements |
| `chi_square` | Qiskit + L2 | Computed from actual circuit measurements |
| `threshold_low/high` | Calibration file | Loaded from frozen `data/thresholds.json` |
| `evidence_id` | API + L4 | Generated by the ledger hash chain |
| `latency_ms` | API timer | Wall-clock time of the verification |
| `detected` | Attacker reporting | `actual_outcome != "ACCEPT"` |
| `http_status` | HTTP client | Actual response code from the API |
| `reason` | API logic | Determined by the rejection layer |
| `calibration_status` | API response | Version of the current calibration |

**Critical guarantee:** The attacker reporting layer **never fabricates** decision, D, chi-square, or evidence_id. These are always extracted from the actual API response. If the API is unreachable, the result contains an `error` field instead.

---

## 11. Calibration

### What calibration does
1. **Baseline computation:** Runs the legitimate QDS circuit many times (e.g., 30 runs × 1024 shots) and computes the mean measurement probabilities (mu) and standard deviations (sigma) for X, Y, Z bases.
2. **Adversarial data:** Runs circuits with disturbance (0.10, 0.25, 0.50) and computes deviation scores.
3. **Threshold search:** Finds tau_low (above all legitimate D scores) and tau_high (in the range of adversarial D scores).
4. **Freeze:** Saves baseline and thresholds to disk. The frozen values are used for all subsequent decisions.

### Why this matters
Without calibration, the system uses hardcoded fallback thresholds. These may not match the actual simulator behavior, leading to incorrect decisions (false accepts or false rejects).

### Blind evaluation
After calibration, we run a **blind evaluation**: a predeclared population of legitimate and adversarial requests against the frozen thresholds. We compute:
- **TP:** Legitimate requests correctly accepted
- **FP:** Adversarial requests incorrectly accepted
- **TN:** Adversarial requests correctly rejected
- **FN:** Legitimate requests incorrectly rejected
- **FAR, FRR, Accuracy, F1, P_forge_emp**

**Why blind testing matters:** If thresholds were tuned on the same data used for evaluation, results would be meaninglessly optimistic. Blind evaluation uses different random seeds.

---

## 12. Statistical Detection

### Deviation D
D measures how far the observed measurement distribution is from the expected baseline:

```
D = Σ (over all bases and outcomes) w × (p_observed - p_expected)²
```

- If D ≈ 0: The measurement pattern looks legitimate
- If D is large: Something has changed the quantum state

### Chi-square (χ²)
A cross-check that accounts for sample size:

```
χ² = Σ N × (p_observed - p_expected)² / p_expected
```

χ² grows with N (shot count), so it captures whether a small deviation is statistically significant or just finite-shot noise.

### Decision boundaries
```
D ≤ τ_low  →  ACCEPT     (within baseline)
τ_low < D ≤ τ_high  →  QUARANTINE  (suspicious)
D > τ_high  →  REJECT     (clear deviation)
```

> **We do NOT claim** that D or χ² alone proves security. They are empirical detection tools operating under the tested threat model.

---

## 13. Evidence Ledger

### How the hash chain works

Each event is stored with two hashes:

```
Event₁
  previous_hash = 0000...0000 (genesis)
  canonical = JSON(all event fields, sorted)
  current_hash = SHA-256(previous_hash + canonical)

Event₂
  previous_hash = Event₁.current_hash
  canonical = JSON(all event fields, sorted)
  current_hash = SHA-256(previous_hash + canonical)

Event₃
  previous_hash = Event₂.current_hash
  ...
```

### What tampering demonstrates
If you change **any field** in **any event**, its `current_hash` no longer matches the recomputed hash. Additionally, all subsequent events have `previous_hash` pointers that no longer chain correctly.

### What this is NOT
This is a **local, append-only, hash-linked evidence log**. It provides tamper **evidence** (you can detect that something was changed), not tamper **prevention**.

It is **NOT**:
- Decentralized blockchain consensus (no distributed nodes)
- Byzantine fault-tolerant (single-point-of-trust: the API)
- Formally proven immutable (an attacker with database access could recompute all hashes)

---

## 14. Docker Testbed

### Container Architecture

| Container | Purpose | Exposed Port |
|---|---|---|
| `qsentinel-api` | FastAPI backend (L1/L2/L3/L4) | None (internal only) |
| `qsentinel-dashboard` | Streamlit Judge Mode UI | `8501` |
| `qsentinel-attacker` | Adversarial HTTP client | None |
| `qsentinel-rdp` | Lightweight desktop for judge | `3389→3000` |

### Network
All containers share the `qsentinel_internal` bridge network. The API is NOT exposed to the host — only the dashboard and RDP have host-facing ports.

### Volumes
`qsentinel_data` — shared volume for:
- `ledger.db` (SQLite evidence database)
- `baseline.json` (calibrated baseline)
- `thresholds.json` (frozen thresholds)

### Security boundary
The attacker container has volume access to `qsentinel_data` for the **ledger tampering** test (which requires direct SQLite modification). All other attacks operate through HTTP only.

---

## 15. Demo Failure Recovery

### "API is not responding"
```bash
make ps                    # Check container status
make logs-api              # Check API logs
docker compose restart qsentinel-api
make ps                    # Verify healthy
```
**Fallback:** Show the code and tests locally: `python -m pytest tests/ -v`

### "Dashboard shows 'Could not reach API'"
```bash
make logs-dashboard        # Check dashboard logs
docker compose restart qsentinel-dashboard
```
**Fallback:** Run attacks from CLI: `make attack-all`

### "Calibration not done"
```bash
make calibrate             # Run Qiskit-based calibration
```
**Fallback:** The system works with uncalibrated fallbacks — just acknowledge it.

### "Attack returns ERROR"
```bash
make logs-api              # Check for Python traceback
make logs-attacker         # Check attacker output
```
**Fallback:** Run the specific attack individually:
```bash
make attack-replay         # Or whichever attack
```

### "Ledger tamper test shows 'chain_valid_UNEXPECTED'"
The database may have been reset. Run a legitimate request first, then retry:
```bash
make attack-ledger
```

### "Docker build fails"
```bash
docker compose build --no-cache
```
**Fallback:** Run the API locally:
```bash
pip install -r requirements.txt
PYTHONPATH=. uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
```

---

## 16. Judge Questions and Answers

### "Why quantum computing?"
Quantum digital signatures use quantum mechanical properties (superposition, entanglement, no-cloning) to provide security guarantees that are different from classical digital signatures. Q-SENTINEL explores how threat detection works in this quantum verification context — specifically, how adversarial actions change observable measurement statistics.

### "Why teleportation?"
Teleportation is the mechanism used to transfer quantum signature states between parties. Our detector monitors the teleported state's measurement statistics. If the teleportation channel is disturbed, the statistics change detectably.

### "Why Qiskit-Aer?"
Qiskit is IBM's open-source quantum computing SDK. Qiskit-Aer provides a high-fidelity classical simulator that executes real quantum circuits. This lets us test our detection pipeline without requiring access to physical quantum hardware, which is expensive and noisy.

### "Why not physical hardware?"
Physical quantum hardware introduces noise (decoherence, gate errors) that would complicate our controlled experiments. The simulator lets us isolate the effects of our specific adversarial manipulations from hardware noise. Moving to hardware is a future goal, not a current requirement.

### "Is this AI?"
No. Q-SENTINEL uses deterministic statistical analysis (deviation D, chi-square) with fixed thresholds. There is no machine learning, no neural network, and no adaptive model.

### "Is this blockchain?"
Not in the decentralized sense. We use a local SHA-256 hash chain for tamper-evident evidence logging — like a cryptographic audit trail. There are no distributed nodes, no mining, and no consensus protocol.

### "Is this a formal QDS security proof?"
No. Q-SENTINEL is an empirical testbed that demonstrates how measurement statistics change under adversarial conditions. Our metrics (D, chi-square, P_forge_emp) are experimental observations, not formal information-theoretic security bounds.

### "How is an attack actually executed?"
Each attack is a Python script that constructs a malicious HTTP request and sends it to the real API. The API processes it through the same L3→L1→L2→L4 pipeline as any request. The attacker script records the actual response.

### "How do you know the logs are real?"
Every logged value comes from the actual API response. The attacker never fabricates decision, deviation score, or evidence_id. You can trace any event from the attacker's JSON through the API logs to the ledger database.

### "How are thresholds chosen?"
Through calibration: we run many legitimate circuits, compute D scores, and set tau_low above the maximum legitimate D. Then we run adversarial circuits and set tau_high in the adversarial range. Thresholds are frozen and not modified during evaluation.

### "How do you avoid test-set leakage?"
Calibration uses one set of random seeds. Blind evaluation uses different seeds. The thresholds are frozen before evaluation begins.

### "What happens during replay?"
The attacker resubmits an identical request (same nonce). L3's nonce guard has already recorded that nonce as "seen," so the second submission is rejected with HTTP 403. No quantum circuit executes.

### "What happens during impersonation?"
The attacker uses an unregistered signer_id. L3's allowlist check fails. Rejected with HTTP 403.

### "What happens during channel manipulation?"
The attacker specifies a disturbance parameter. The API injects rx/rz rotation gates into the Qiskit circuit before measurement. The measurement statistics shift. L2 computes a higher D and may QUARANTINE or REJECT.

### "What happens if the ledger is modified?"
The hash chain breaks. Each event's hash depends on the previous event's hash plus its own content. Changing any field invalidates the hash, and chain verification reports the exact point of tampering.

### "What is your biggest limitation?"
We simulate quantum circuits rather than running on real hardware. Our "channel attack" is a controlled parameter, not a real quantum channel interception. Our signature validity check uses a testbed flag, not full cryptographic verification.

### "How would this move to real quantum hardware?"
Replace `AerSimulator` with a real IBM Quantum backend in `TeleportationQDS.__init__`. The circuit construction, measurement, and statistical pipeline remain identical. Hardware noise would require recalibration of thresholds.

---

## 17. Scientific Claims Boundary

### ✅ WHAT WE CLAIM
- We execute **real quantum circuits** on the Qiskit-Aer simulator
- Measurement results are **actual simulator output**, not fabricated
- Statistical detection (D, χ²) is computed from **real measurement distributions**
- Channel disturbance **measurably changes** the quantum circuit's output
- The hash-chain ledger **detects tampering** of stored events
- L3 security guards **functionally reject** unauthorized/replayed requests
- The testbed is **reproducible** via Docker

### ❌ WHAT WE DO NOT CLAIM
- This is NOT a formal QDS security proof
- This does NOT run on real quantum hardware
- Channel manipulation is NOT external quantum channel interception
- Signature validity is NOT cryptographic verification
- The ledger is NOT decentralized blockchain
- P_forge_emp is NOT an information-theoretic bound
- Detection thresholds are NOT proven optimal
- The system does NOT use AI/ML

---

## 18. 3-Minute Demo Version

1. **30s:** Show dashboard, explain "every button is a real attack"
2. **30s:** Click LEGITIMATE → show ACCEPT, point at D ≈ 0
3. **30s:** Click REPLAY → show REJECT, explain nonce reuse
4. **30s:** Click CHANNEL → show three disturbance levels, point at increasing D
5. **30s:** Click TAMPER LEDGER → show integrity violation
6. **30s:** Say: *"We run real Qiskit circuits, compute real statistics, and record tamper-evident evidence. No AI, no fake logs."*

---

## 19. 7-Minute Deep Technical Demo

1. **1m:** Architecture overview (draw the L3→L1→L2→L4 pipeline)
2. **1m:** LEGITIMATE request — walk through D, chi-square, baseline
3. **30s:** REPLAY — explain nonce guard
4. **30s:** IMPERSONATION — explain allowlist
5. **1m:** CHANNEL low/medium/high — show D increasing, explain rx/rz injection
6. **30s:** FORGERY A — explain the honest limitation
7. **30s:** FORGERY B — explain P_forge_emp
8. **30s:** LEDGER TAMPER — show hash chain break
9. **30s:** Show calibration command and explain threshold derivation
10. **30s:** Final slide: Claims boundary — what we claim vs what we don't

---

## 20. Final Judge Takeaway

Q-SENTINEL demonstrates that **quantum measurement statistics can serve as a threat detection signal** in QDS verification.

By executing real Qiskit circuits and comparing observed distributions against calibrated baselines, we show that:
- **Adversarial channel manipulation** produces measurably different statistics
- **Classical security controls** (nonce, identity, authorization) protect the quantum verification pipeline
- **Tamper-evident logging** provides an audit trail for every decision

This is not a production system. It is not a formal security proof. It is a **working, honest, reproducible testbed** that demonstrates the concept and survives hostile technical questioning.
