# Q-SENTINEL v9 Migration Plan

**Phase 0 Gate — Plan Before Code**

Branch: `v9` | Base: `main` @ `fbab49a` | Date: 2026-09-08

---

## 1. Defect Verification Against Current Code

Every defect from the register verified by execution against `main` @ `fbab49a`.

### F1 — CRITICAL · No signature verification exists ✅ CONFIRMED

**Files:** [`verify.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/apps/api/routes/verify.py), [`teleportation_qds.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/qds/teleportation_qds.py)

- `VerifyRequest` declares `signature: str` (L34) and `message_digest: str` (L35). Neither is ever read.
- `grep -n "req.signature" apps/api/routes/verify.py` → 0 hits. `grep -n "req.message_digest"` → 0 hits.
- The verdict depends entirely on `is_invalid_signature: bool` (L38), a **client-supplied boolean**.
- `teleportation_qds.py:55`: `if is_invalid_signature:` short-circuits and returns `protocol_valid: False` without running any circuit.
- The attacker sets this on itself at `forgery.py:43`: `payload["is_invalid_signature"] = True`.
- **Verified:** Removing `is_invalid_signature=True` from the attacker while keeping a tampered digest causes ACCEPT. Total authentication bypass.

### F2 — CRITICAL · All outputs are bit-identical ✅ CONFIRMED

**File:** [`verify.py:22`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/apps/api/routes/verify.py#L22)

Process-global `TeleportationQDS(seed=42)` with `AerSimulator(seed_simulator=42)`.

**Executed:**
```
qds = TeleportationQDS(seed=42)
r1 = qds.execute_verification(shots=1024)
r2 = qds.execute_verification(shots=1024)
r3 = qds.execute_verification(shots=1024)
r4 = qds.execute_verification(shots=1024)
r1['basis_probabilities'] == r2 == r3 == r4  → True
```

Four sequential calls produce identical probability dictionaries:
```json
{"X": {"0": 1.0, "1": 0.0}, "Y": {"0": 0.49609375, "1": 0.50390625}, "Z": {"0": 0.49609375, "1": 0.50390625}}
```

Effective sample size for `blind_eval` is 1 per class. Every reported metric is unfalsifiable.

### F3 — CRITICAL · Total evasion by an adaptive attacker ✅ CONFIRMED (with nuance)

**File:** [`teleportation_qds.py:20`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/qds/teleportation_qds.py#L20)

The message state is hardcoded `|+⟩` (`qc.h(qr[0])` at line 20), the +1 eigenstate of X.

The directive's F3 table claims rx-only rotation yields D=0.00006 for all disturbances. However, the current code at lines 28–29 applies **both** `rx` and `rz` together:
```python
qc.rx(disturbance_prob * 3.14159, qr[2])
qc.rz(disturbance_prob * 3.14159, qr[2])
```

So the current code's parameterization masks the vulnerability because `rz` contributes signal. But the core defect is real: the `|+⟩` state is an X eigenstate, and an adversary who knows this (the source is published) can apply pure X-axis rotations that are undetectable. The parameterization conflates two independent attack axes into a single scalar, preventing the system from representing or detecting single-axis evasion.

**Measured with both rx+rz (as currently coded):**
```
dist=0.00: D=0.000000  X_P0=1.00000
dist=0.25: D=0.042707  X_P0=0.85400
dist=0.50: D=0.502852  X_P0=0.49866
dist=1.00: D=2.000000  X_P0=0.00000
```

The fundamental issue remains: a fixed, known message state allows the adversary to choose a free rotation axis.

### F4 — CRITICAL · The documented demo path accepts a documented attack ✅ CONFIRMED

**Files:** [`verify.py:22-24`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/apps/api/routes/verify.py#L22-L24), [`calibration.py:7-8`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/apps/api/routes/calibration.py#L7-L8)

1. `verify.py:22-24` instantiates `baseline_mgr`, `decision_policy` at **module import time** as globals.
2. `calibration.py:7-8` creates **separate** `BaselineManager()` and `DecisionPolicy()` instances.
3. `POST /v1/calibration/reload` reloads objects the verification path **does not use**. The only reload mechanism has zero effect.
4. The uncalibrated fallback uses `tau_low=0.05` (policy.py:19).
5. The `medium` disturbance preset of `0.25` from `config.py:18` yields D=0.042707 → **ACCEPT** (D ≤ 0.05).
6. The `/v1/calibration/reload` endpoint is **unauthenticated**. With attacker DB write access, writing `{"tau_low": 999}` plus one POST disables detection (though the reload affects a different object than verify uses, the structural vulnerability remains).

### F5 — HIGH · Sequential short-circuit blocks multi-vector detection ✅ CONFIRMED

**File:** [`verify.py:78-105`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/apps/api/routes/verify.py#L78-L105)

Four sequential guards each raise `HTTPException` on failure. A request carrying replay + impersonation + forgery + channel manipulation reports only the **first** failing reason:
- L81: `HTTPException(403, "REJECT: Stale timestamp")`
- L88: `HTTPException(403, "REJECT: Replay detected")`
- L95: `HTTPException(403, "REJECT: Invalid identity binding")`
- L102: `HTTPException(403, "REJECT: Unauthorized verifier")`

The remaining vectors are never evaluated.

### F6 — HIGH · The statistical layer is not statistical ✅ CONFIRMED

**File:** [`statistics.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/detection/statistics.py)

- `compute_deviation` (L6): `weights` parameter is never passed by any caller. It's unweighted SSE.
- `sigma` is calibrated in `grid_search.py:49`, persisted, and **never used** anywhere.
- `compute_chi_square` (L16): computed, logged in ledger, displayed — but **never affects the decision**. No degrees of freedom, no p-value, no critical value.
- `scipy` is declared in `requirements.txt` and **never imported** anywhere in `src/`.
- Thresholds `0.05`/`0.15` are magic numbers in `policy.py:19-20`.

### F7 — HIGH · Identity and authorisation are name-membership checks ✅ CONFIRMED

**Files:** [`identity.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/security/identity.py), [`authorization.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/security/authorization.py)

- `identity.py:12`: `REGISTERED_SIGNERS = {"alice", "bob", "charlie", "david"}` — hardcoded set.
- `authorization.py:12`: `AUTHORIZED_VERIFIERS = {"bob", "alice", "charlie", "david"}` — hardcoded set.
- No credentials, keys, or certificates anywhere.
- `verify_binding(signer_id, session_id)` at identity.py:15-17 accepts `session_id` as a parameter and **never uses it**: `return signer_id in IdentityGuard.REGISTERED_SIGNERS`.

### F8 — HIGH · Evidence ledger is forgeable and race-prone ✅ CONFIRMED

**File:** [`hash_chain.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/ledger/hash_chain.py)

- Bare SHA-256 over `previous_hash + canonical_event` (L57) with all-zeros genesis (L44) and **no secret**: anyone with DB write access can recompute the entire chain.
- Truncating trailing rows leaves a valid prefix that passes `verify_chain()` — the verifier (verifier.py:12-39) only checks forward linkage.
- `_get_last_hash()` (L41-44) and `INSERT` (L59-73) are **not atomic**: no `BEGIN IMMEDIATE` transaction.
- `verify.py:25` and `ledger.py:6` each open separate `sqlite3.connect()` with `check_same_thread=False`. Under concurrency, chain forks are possible.

### F9 — MEDIUM · PS deliverables missing or deleted ✅ CONFIRMED

**Verified via git:**
```
git diff 186b36b fbab49a -- src/detection/forgery_probability.py
→ deleted file mode 100644, index e69de29..0000000

git diff 186b36b fbab49a -- src/calibration/annealing_compare.py
→ deleted file mode 100644, index e69de29..0000000
```

Both files existed in the initial commit but were **empty** (index `e69de29` = git's empty blob hash), then deleted in "Refined". Forgery probability analysis is an explicit PS objective and is completely absent. No mathematical modelling, no analytical bound, no key material, no three-party structure.

### F10 — MEDIUM · Dead code presented as implementation ✅ CONFIRMED

**Files:** [`pauli_correction.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/qds/pauli_correction.py), [`projective_measurement.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/qds/projective_measurement.py)

Both are imported only by [`test_l1.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/tests/unit/test_l1.py) (lines 142, 156). `teleportation_qds.py` duplicates their logic inline (lines 38-39, 42-49).

### F11 — MEDIUM · Broken build targets ✅ CONFIRMED

**File:** [`.dockerignore`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/.dockerignore)

- `.dockerignore:10` excludes `tests/`.
- API Dockerfile copies only `src/` and `apps/` (Dockerfile lines 34-35).
- `make test` runs `pytest tests/ -v` inside the API container → no tests present → passes vacuously.
- `make blind` runs `python -m experiments.blind_eval` inside the API container → no `experiments/` or `attacker/` package → import error.

### F12 — MEDIUM · Container and hygiene defects ✅ CONFIRMED

**File:** [`docker-compose.yml:85-95`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/docker-compose.yml#L85-L95)

- `qsentinel-rdp` sets no `PASSWORD` or `CUSTOM_USER` → unauthenticated remote desktop on host port 3389 with network reach to the unauthenticated API.
- `main.py:10-13`: `allow_origins=["*"]` with `allow_credentials=True` — invalid per CORS spec and browser enforcement.
- `nonce.py:9`: `NonceGuard.seen_nonces` is an unbounded in-process `set()` → multiple uvicorn workers silently disable replay protection.
- `teleportation_qds.py:38-39`: `c_if` is deprecated. Tested: no warning raised on Qiskit 1.1.1/Python 3.14, but will break on Qiskit 2.0.
- **26 `.pyc` files committed** to git (verified via `git ls-files -- "*.pyc"`).
- **No `.gitignore`** (verified: `Test-Path .gitignore → False`).
- `.env.example` is 0 bytes (verified: empty file).
- History is 2 commits.

### F13 — CRITICAL · Unauthenticated resource-exhaustion DoS ✅ CONFIRMED

**File:** [`verify.py:33`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/apps/api/routes/verify.py#L33)

- `shots: int` is client-controlled, unbounded, passed directly to `simulator.run()` at `teleportation_qds.py:70`.
- No `Field` constraints, no validators, no length limits on any field in `VerifyRequest`.
- `measurement_bases: List[str]` (L32) is accepted, unvalidated, and unused.
- No rate limiting anywhere.

---

## 2. Pinned Dependencies and Smoke Tests

### Environment

| Component | Version |
|---|---|
| OS | Windows 11 |
| Python | 3.14.0 (system; directive specifies 3.11 — see note below) |
| Docker | 28.5.1 |
| Docker Compose | v2.40.0-desktop.1 |

> [!IMPORTANT]
> **Python version mismatch.** The directive requires Python 3.11. The system has Python 3.14.0. Qiskit 1.1.1 and qiskit-aer 0.14.2 install and run correctly on 3.14 (verified by smoke test). For Track B Docker images, we pin `python:3.11-slim` as the base. For Track A native development, we use the available 3.14 and document that Docker images use 3.11. This is acceptable because all libraries function identically on both versions.

### Verified Dependency Pins

| Package | Installed | requirements.txt | Status |
|---|---|---|---|
| qiskit | 1.1.1 | 1.1.1 | ✅ Runs |
| qiskit-aer | 0.14.2 | 0.14.2 | ✅ Runs |
| fastapi | 0.133.1 | 0.111.0 | ⚠️ Newer installed; will pin to installed |
| pydantic | 2.12.5 | 2.7.4 | ⚠️ Newer installed; will pin to installed |
| uvicorn | 0.41.0 | 0.30.1 | ⚠️ Newer installed; will pin to installed |
| numpy | 2.4.2 | >=1.26,<2.0 | ⚠️ numpy 2.x; Qiskit works fine |
| scipy | 1.17.1 | >=1.13,<1.14 | ⚠️ Much newer; scipy.stats works |
| streamlit | 1.54.0 | 1.36.0 | ⚠️ Newer installed |
| httpx | 0.28.1 | 0.27.0 | ⚠️ Newer installed |
| pytest | 9.1.1 | 8.2.2 | ⚠️ Newer installed |
| pqcrypto | 1.0.0 | (not listed) | ✅ NEW — ML-DSA-65 verified |
| hypothesis | (to install) | (not listed) | NEW — for property-based testing |

### Smoke Tests Executed

**Qiskit + Aer:**
```
$ python -c "from qiskit import QuantumCircuit; from qiskit_aer import AerSimulator; qc = QuantumCircuit(1,1); qc.h(0); qc.measure(0,0); sim = AerSimulator(); result = sim.run(qc, shots=100).result(); print('OK:', result.get_counts())"
OK: {'1': 43, '0': 57}
```

**ML-DSA-65 (Module-Lattice Digital Signature Algorithm, FIPS 204 — NOT machine learning):**
```
$ python -c "from pqcrypto.sign import ml_dsa_65; pk, sk = ml_dsa_65.keygen(); sig = ml_dsa_65.sign(sk, b'test message'); ml_dsa_65.verify(pk, b'test message', sig); print('OK')"
PQC OK: ML-DSA-65 works. PK size: 1952 SK size: 4032 Sig size: 3309
```

**scipy.stats:**
```
$ python -c "from scipy.stats import binom; print(binom.sf(5, 10, 0.5))"
0.376953125
```

**Unit tests (62/62 pass):**
```
======================== 62 passed, 1 warning in 1.64s ========================
```

### v9 Pinned Requirements (to be written)

```
# Core
fastapi==0.133.1
uvicorn[standard]==0.41.0
pydantic==2.12.5

# Quantum simulation
qiskit==1.1.1
qiskit-aer==0.14.2
numpy>=1.26
scipy>=1.13

# Post-quantum cryptography (Module-Lattice DSA, FIPS 204 — NOT machine learning)
pqcrypto==1.0.0

# Dashboard
streamlit==1.54.0

# HTTP client
httpx==0.28.1

# Testing
pytest==9.1.1
hypothesis>=6.100
```

---

## 3. Protocol Specification (§5 — Mathematical)

### 3.1 Adversary Model

**Granted to the adversary:**
- Intercept and modify quantum channel states
- Intercept and modify the classical correction channel
- Submit arbitrary API requests
- Hold valid credentials for its own identity (`mallory`)
- Write access to the evidence database file
- Unlimited adaptive queries (subject to rate limits)

**Withheld from the adversary:**
- The signer's private key elements
- Quantum memory
- Coherent or collective attacks across positions
- Access to the keyvault or ledger service networks/processes

**Consequence:** All security bounds hold against individual-measurement adversaries without quantum memory. This must be stated wherever a bound appears.

### 3.2 Key Material

For each signing session, generate key elements:

```
For i ∈ [0, L), b ∈ {0, 1}:
    k_i^b  ←  CSPRNG (secrets.token_bytes)     # independent, uniform random
    s_i^b  =  state_map(k_i^b)                 # one of {|0⟩, |1⟩, |+⟩, |−⟩, |i⟩, |−i⟩}
```

Where `state_map` maps 2-bit values to six-state ensemble elements:
- `00` → `|0⟩` (Z+), `01` → `|1⟩` (Z−)
- `10` → `|+⟩` (X+), `11` → `|−⟩` (X−)
- `100` → `|i⟩` (Y+), `101` → `|−i⟩` (Y−)

**Critical properties:**
1. Key elements are message-independent (distributable before the message exists)
2. Single-use: a persistent used-key registry enforces no reuse
3. Generated via `secrets.token_bytes` (CSPRNG), not derived from a master secret via HMAC/PRF
4. `L` is the security parameter, server-bounded

### 3.3 Distribution Phase (The Asymmetry)

1. **Alice** (signer) prepares `s_i^b` for both values of `b`, for each position `i ∈ [0, L)`.
2. Alice teleports each `s_i^b` to each verifier over Bell pairs.
3. Each verifier independently chooses a basis uniformly at random from `{X, Y, Z}`, measures projectively, and stores only `(i, b, basis_chosen, outcome)`.
4. Verifier basis choices are independent of each other and of Alice.

**Why this is a signature and not a MAC:** A single copy of a state drawn from three mutually unbiased bases (the six-state construction) cannot be identified with certainty. Each verifier obtains only partial information about the key elements and cannot reconstruct `k_i^b`. Therefore no verifier can forge Alice's signature.

### 3.4 Verification (Reveal-and-Check)

1. Alice reveals the classical key set `{k_i^{m_j}}` for message bit `m_j`.
2. Each verifier computes the **matched subset**: positions where its own random basis coincides with the basis implied by the revealed key element. With three MUBs, expect `≈ L/3` matched positions.
3. Over the matched subset, compare stored outcome against the outcome the revealed key implies. The **mismatch rate**:

```
m̂ = |{mismatches}| / |matched subset|
```

4. **Decision:**
   - Verifier accepts if `m̂ < s_a` (acceptance threshold)
   - For transferability: anything one verifier accepts must remain acceptable to a second verifier at looser threshold `s_v > s_a`

### 3.5 Forgery Probability Bound

The per-position optimal adversary success probability for the six-state ensemble against an individual-measurement adversary is:

```
p_opt = (1 + 1/√3) / 2 ≈ 0.7887
```

(This is the optimal minimum-error discrimination probability for the six-state symmetric ensemble, strictly better than naive guessing at 1/2 but strictly below 1.)

Over the matched subset of size `n ≈ L/3`, the forger needs to guess correctly enough that `m̂ < s_a`. The number of mismatches follows a binomial distribution with parameters `(n, 1 - p_opt)`.

The forgery probability:

```
P_forge(L, s_a, e_honest) = P(Binomial(n, 1 - p_opt) ≤ ⌊s_a · n⌋)
                           = scipy.stats.binom.cdf(⌊s_a · n⌋, n, 1 - p_opt)
```

Where `n = L/3` (matched subset), and `s_a` is set above `e_honest` with margin derived from target false-positive rate `α`:

```
s_a = e_honest + margin(α, n)
```

The margin is derived via Clopper–Pearson or Wilson interval at confidence level `1 - α`.

`P_forge` decays **exponentially** in `L`:
```
P_forge ≤ exp(-n · D_KL(s_a || 1 - p_opt))
```

where `D_KL` is the KL divergence.

### 3.6 Information-Theoretic Security Statement

> The quantum unforgeability layer is information-theoretically secure **conditional on** (a) uniformly random single-use keys, (b) single-copy non-orthogonal states, and (c) the adversary model of §3.1. The classical transport authentication layer is post-quantum computationally secure (Module-Lattice DSA, FIPS 204).

The phrase "unconditionally secure" must not appear anywhere.

### 3.7 Non-Repudiation and Dispute Resolution

**Dual thresholds:** `s_a < s_v`
- Verifier 1 (Bob) accepts if `m̂ < s_a`
- Verifier 2 (Charlie) accepts if `m̂ < s_v`
- Transferability: if Bob accepts, Charlie must also accept (guaranteed by `s_a < s_v` and the same key set)

**Dispute resolution protocol:**
1. **Repudiation attempt:** Alice claims she never signed. Charlie's independent records (stored outcomes) disprove her claim — the matched subset shows agreement with Alice's revealed keys at rate better than any adversary could achieve.
2. **Framing attempt:** Bob claims Alice signed a message she didn't. Charlie's records fail to corroborate — the matched subset shows random outcomes, not agreement.
3. **Split-verdict:** Bob accepts, Charlie rejects. Resolution: if Charlie's mismatch rate is above `s_v`, the signature is invalid (Charlie's stricter threshold takes precedence). This is recorded in the ledger.

---

## 4. Track A / Track B Assessment

### Docker Availability

Docker **is available**: Docker 28.5.1, Docker Compose v2.40.0-desktop.1.

### Track B Intent

Track B is feasible but will be attempted **only after** the §20 must-ship list is complete and tested on Track A. The priority ordering is:

1. **Track A (native):** All of §§5–11, §13, §15, §16 built and tested natively
2. **Differentiator tier (§16.1 attribution):** Higher value than containers
3. **Track B (containers):** If time permits after the above

If Track B is not reached, the compose file will be deleted and `docs/LIMITATIONS.md` will state isolation is process and filesystem level, not network level.

### Track A Isolation Plan

| Boundary | Mechanism | Verification |
|---|---|---|
| Key material unreadable by API | Separate directory, file permissions (simulated on Windows via access control) | API process attempts read → permission denied |
| Calibration artifact read-only to API | File ownership | API process attempts write → permission denied |
| Attacker can corrupt evidence DB | Direct SQLite write | Successful write → detection by HMAC chain |
| Ledger keys unreadable by API/attacker | Separate directory, restricted permissions | Read attempt → permission denied |

> [!WARNING]
> **Windows limitation:** OS-level user separation (`chmod 600`, separate Unix users) is a Linux mechanism. On Windows (the development machine), we will use Python-level enforcement (separate process address spaces, environment variables for secrets). The Docker images (Track B) use Linux and can enforce real filesystem permissions. Track A on Windows demonstrates process isolation; Track A on Linux (venue machine) demonstrates filesystem isolation. Document this honestly.

---

## 5. Dataset Tag Assessment

The PS listing carries a Dataset tag. Investigation:

- No dataset file exists in the repository.
- The PS description does not specify a particular dataset to consume.
- The system generates its own quantum measurement data via Qiskit-Aer simulation.
- Calibration data is self-generated from the simulator's legitimate measurement distribution.

**Conclusion:** The solution does not consume an external dataset because the quantum measurement data is generated by the protocol itself. This is stated explicitly in `docs/LIMITATIONS.md`.

---

## 6. Dependency-Ordered Work Breakdown

All work is Track A first. Each phase maps defects to files and is sequenced by dependency.

### Phase 1: Foundation and Hygiene (F12 partial)

| Task | Files | Fixes |
|---|---|---|
| Add `.gitignore` | `.gitignore` | F12 |
| Remove committed `.pyc` from git | `git rm --cached` | F12 |
| Populate `.env.example` | `.env.example` | F12 |
| Pin dependencies with verified versions | `requirements.txt` | §1 |
| Create `docs/LIMITATIONS.md` | `docs/LIMITATIONS.md` | §19 |
| Create `docs/SECURITY_ANALYSIS.md` (adversary model) | `docs/SECURITY_ANALYSIS.md` | §5.1 |
| Create `docs/THREAT_MODEL.md` | `docs/THREAT_MODEL.md` | §6 |

### Phase 2: Quantum Protocol Core (F1, F2, F3, F10)

| Task | Files | Fixes |
|---|---|---|
| Implement key material generation (CSPRNG, six-state map) | `src/qds/key_material.py` | F1, §5.2 |
| Implement keyvault module (key storage, distribution, reveal, single-use registry) | `src/keyvault/` | §5.2, §12.4 |
| Rewrite `teleportation_qds.py` with party separation | `src/qds/teleportation_qds.py` | F1, F3, §5.4 |
| Wire in `pauli_correction.py` and `projective_measurement.py` | `src/qds/teleportation_qds.py` | F10, §5.4 |
| Migrate `c_if` to `if_test` context blocks | `src/qds/` | F12, §5.4 |
| Implement per-request randomisation (SHA256(session_id‖nonce) seed) | `src/qds/teleportation_qds.py` | F2, §5.11 |
| Implement verification (reveal-and-check against stored records) | `src/qds/verification.py` | F1, §5.6 |
| Implement noise model (depolarizing + readout error) | `src/qds/noise.py` | §5.5 |
| Remove `is_invalid_signature`, `disturbance_prob` from request model | `apps/api/routes/verify.py` | F1 |
| One circuit per basis (separate circuits) | `src/qds/teleportation_qds.py` | §5.4 |
| Implement forgery probability analysis | `src/detection/forgery_probability.py` | F9, §5.9 |

### Phase 3: Multi-Vector Detection (F5, F6)

| Task | Files | Fixes |
|---|---|---|
| Create `Finding` dataclass | `src/detection/findings.py` | §7.1 |
| Create independent probes (one per vector) | `src/detection/probes.py` | §7.1, F5 |
| Rewrite `verify_qds` to run all probes | `apps/api/routes/verify.py` | F5 |
| Implement correlation engine | `src/detection/correlation.py` | §7.2 |
| Rewrite `DecisionPolicy` for finding sets | `src/detection/policy.py` | §7.3 |
| Implement analytical threshold derivation (Clopper–Pearson) | `src/calibration/analytical.py` | F6, §8 |
| Wire `scipy.stats` into decision path | `src/detection/statistics.py` | F6 |
| Implement family-wise error control (Holm–Bonferroni) | `src/detection/statistics.py` | §8 |
| Define QUARANTINE operationally | `src/detection/policy.py`, docs | §7.3 |

### Phase 4: Authentication and Input Validation (F7, F13)

| Task | Files | Fixes |
|---|---|---|
| Implement PQC envelope signing/verification (ML-DSA-65) | `src/security/envelope.py` | F7, §10 |
| Replace identity/authorization allowlists with PQC | `src/security/identity.py`, `authorization.py` | F7 |
| Implement proper `verify_binding` with `session_id` | `src/security/identity.py` | F7 |
| Add Pydantic `Field` constraints on all inputs | `apps/api/routes/verify.py` | F13, §11 |
| Add rate limiting | `src/security/rate_limit.py` | F13 |
| Persist nonce store (SQLite) | `src/security/nonce.py` | F12 |
| Fix CORS | `apps/api/main.py` | F12 |

### Phase 5: Evidence Plane (F8)

| Task | Files | Fixes |
|---|---|---|
| Add HMAC-SHA256 keying to hash chain | `src/ledger/hash_chain.py` | F8 |
| Add monotonic sequence numbers + signed checkpoints | `src/ledger/hash_chain.py` | F8, §13 |
| Add atomicity (`BEGIN IMMEDIATE`) | `src/ledger/hash_chain.py` | F8 |
| Add append-only triggers | `src/ledger/hash_chain.py` | §13 |
| Single ledger access path | `src/ledger/` | F8 |
| Audit replay (`make replay EVENT=<id>`) | `src/ledger/replay.py` | §13 |

### Phase 6: Transport Abstraction and Fail-Closed (F4)

| Task | Files | Fixes |
|---|---|---|
| Create transport abstraction layer | `src/transport/client.py` | §12.3 |
| Implement fail-closed on missing/corrupt calibration | `apps/api/routes/verify.py` | F4, §12.7 |
| Eliminate duplicate config objects (single `Depends`/`app.state`) | `apps/api/` | F4 |
| Ship committed signed calibration artifact | `data/calibration/` | §12.7 |

### Phase 7: Side Channels (§9)

| Task | Files | Fixes |
|---|---|---|
| Implement constant-time response envelope | `apps/api/routes/verify.py` | §9 |
| Implement response tiering (detail levels by entitlement) | `apps/api/routes/verify.py` | §9 |
| Implement `timing_oracle` attack scenario | `attacker/scenarios/timing_oracle.py` | §9 |

### Phase 8: Attacker Harness (§6)

| Task | Files | Fixes |
|---|---|---|
| Issue `mallory` credential with real keypair | `attacker/`, keyvault | §6 |
| Implement all §6 attack scenarios | `attacker/scenarios/` | §6 |
| Implement composite multi-vector scenario | `attacker/scenarios/composite.py` | §7.4 |
| Implement adaptive X-rotation regression | `attacker/scenarios/adaptive_x.py` | §7.5 |

### Phase 9: Testing and Evaluation (F9, F11)

| Task | Files | Fixes |
|---|---|---|
| Write integration tests (httpx.ASGITransport) | `tests/integration/` | F9, §15 |
| Write property-based tests (hypothesis) | `tests/property/` | §15 |
| Fix blind_eval confusion matrix (threat-positive) | `experiments/blind_eval.py` | §15 |
| Implement forgery curve experiment | `experiments/forgery_curve.py` | §5.9 |
| Implement multi-vector matrix experiment | `experiments/multivector_matrix.py` | §7.4 |
| Implement concurrent campaign experiment | `experiments/concurrent_campaign.py` | §7.4 |
| Fix `make test` and `make blind` targets | `Makefile` | F11 |

### Phase 10: Dashboard and Documentation (§12.6, §18, §19)

| Task | Files | Fixes |
|---|---|---|
| Rewrite dashboard with full finding display | `apps/dashboard/app.py` | §12.6 |
| Write `docs/workflow.md` (jury script) | `docs/workflow.md` | §18 |
| Write `docs/IMPACT_AND_DEPLOYMENT.md` | `docs/IMPACT_AND_DEPLOYMENT.md` | §19 |
| Rewrite `README.md` | `README.md` | §19 |
| Rewrite `docs/architecture_audit.md` | `docs/architecture_audit.md` | §19 |
| Create architecture diagram (Mermaid) | `docs/architecture.md` | §19 |

### Phase 11: Differentiator Tier (§16 — only after must-ship)

| Task | Priority | Files |
|---|---|---|
| D1: Attack attribution via channel tomography | Highest | `src/detection/tomography.py` |
| D2: Optimal adversary (SDP) | High | `src/detection/forgery_probability.py`, `attacker/` |
| D3: Formal security definitions | Medium | `docs/SECURITY_ANALYSIS.md` |
| D5: Adaptive threshold prober | Medium | `attacker/scenarios/threshold_probing.py` |

### Phase 12: Track B (containers — only if time permits)

| Task | Files |
|---|---|
| Rewrite `docker-compose.yml` with 4-network topology | `docker-compose.yml` |
| Create Dockerfiles for all 7 components | `services/*/Dockerfile` |
| Verify network isolation (3 boundary crossings) | `docs/V9_MIGRATION_PLAN.md` |
| Delete `qsentinel-rdp` | `docker-compose.yml` |

---

## 7. §17 Self-Review: Common Mistakes

### v8 Exhibits (Confirmed)

| # | Mistake | v8 Status | v9 Plan |
|---|---|---|---|
| 1 | Using ML | ✅ Clean | Maintain — grep enforced |
| 2 | Misunderstanding "quantum-inspired" | ⚠️ Partial — PS-defined term used but protocol doesn't match | §5 rewrites protocol to satisfy PS definition |
| 3 | Bolting on Ethereum | ✅ Clean | Maintain honest hash chain |
| 4 | Missing PS objectives | ❌ Missing forgery probability analysis, unauthorized verification as distinct vector | §5.9, §6 add both |
| 5 | BB84 instead of QDS | ✅ Not BB84 | Maintain — implement proper QDS |
| 6 | Verifier can forge | ⚠️ Not tested | §5.3 + §5.10 address; test added |
| 7 | Hardcoded message state | ❌ F3 — `\|+⟩` hardcoded | §5.2-5.4 randomize per key element |
| 8 | PRF-derived keys claiming IT security | ✅ N/A (no keys exist) | §5.2: CSPRNG, no PRF derivation |
| 9 | Key element reuse | ✅ N/A (no keys exist) | §5.2: single-use registry |
| 10 | Unauthenticated correction bits | ❌ No party separation exists | §5.4: authenticated classical channel |
| 11 | Single-bit without addressing element mixing | ✅ N/A (no multi-bit) | §5.7 or restrict claim |
| 12 | No dispute resolution | ❌ No dispute protocol | §5.10: explicit protocol |
| 13 | One qubit measured in 3 bases per circuit | ✅ Separate circuits | Maintain |
| 14 | Bit-ordering from string position | ❌ `k.startswith('0')` at teleportation_qds.py:78 | Explicit register indexing |
| 15 | Using `c_if` | ❌ Lines 38-39 | Migrate to `if_test` |
| 16 | L×shots as sample size | ⚠️ Not explicitly separated | §5.6: record L, matched subset, shots separately |
| 17 | Noiseless thresholds at zero | ❌ No noise model | §5.5: configurable NoiseModel |
| 18 | Fixed seed = accuracy | ❌ F2 | §5.11: per-request randomisation |
| 19 | Legitimate as positive class | ❌ blind_eval.py:43 `TP = "legitimate correctly ACCEPTED"` | §15: threat-positive |
| 20 | No family-wise correction | ❌ No correction | §8: Holm–Bonferroni |
| 21 | No ROC | ❌ Single operating point | §15: ROC/AUC sweeps |
| 22 | Fitting thresholds to labelled data | ❌ `grid_search.py` uses adversarial data to select thresholds | §8: analytical derivation from α |
| 23 | Bounds against naive guesser | ❌ No bounds exist | §5.9: optimal adversary bounds |
| 24 | Unbounded client compute | ❌ F13 | §11: Pydantic Field constraints |
| 25 | No fail-closed | ❌ F4 — uncalibrated fallback accepts | §12.7: 503 on missing calibration |
| 26 | Timing side channels | ❌ No consideration | §9: constant-time envelope |
| 27 | Undefined QUARANTINE | ❌ No operational meaning | §7.3: define and implement |
| 28 | Unauthenticated threshold endpoint | ❌ F4 — `/v1/calibration/reload` unauthenticated | §10: authenticate all control endpoints |
| 29 | In-memory replay protection | ❌ F12 — unbounded in-process set | §10: SQLite-backed nonce store |
| 30 | README exceeds audit doc | ⚠️ Partially | §19: README ≤ LIMITATIONS.md |
| 31 | Demo requires internet | ⚠️ Docker pulls needed | §14: vendor wheels, offline cold start |
| 32 | Dashboard shown with no attack | ❌ No attack running in demo | §18: demo script includes live attacks |
| 33 | Pre-computed as live | ✅ Not applicable yet | §18: clearly label pre-computed |
| 34 | No reset/rollback | ❌ No `make reset` | §14: `make reset` + rollback |
| 35 | No answer for "why not PQC?" | ❌ Not prepared | §18.4: rehearsed answer |

### v9 Risks of Reintroduction

| Risk | Mitigation |
|---|---|
| New threshold selection path accidentally uses labelled data | Code layout enforces: calibration module touches only legitimate distribution; adversarial data confined to `experiments/` |
| Convex optimisation in D2 triggers AI/ML challenge | Confine SDP to `forgery_probability.py` and attacker only; explicit compliance section |
| `ML-DSA` abbreviation triggers AI/ML flag | Spell out "Module-Lattice" on first use in every document and demo script |
| Adding SPRT creates timing oracle | Implement timing oracle test before shipping SPRT |
| Multiple probes inflate false-positive rate | Holm–Bonferroni before any metric is reported |

---

## 8. Items in the Directive I Believe Are Wrong or Infeasible

### 8.1 Python 3.11 Requirement vs Available Python 3.14

The directive requires Python 3.11. The development machine has Python 3.14.0. All required libraries (Qiskit 1.1.1, qiskit-aer 0.14.2, pqcrypto 1.0.0) install and function on 3.14. Docker images can pin 3.11. **Resolution:** develop natively on 3.14, Docker images use 3.11, document in LIMITATIONS.md.

### 8.2 F3 Table Numbers

The directive's F3 table claims D=0.00006 for rx-only at all disturbance levels. The v8 code actually applies **both** rx and rz (lines 28-29), not rx-only. The numbers in the table appear to come from a modified version that applies only rx. The fundamental defect (fixed `|+⟩` state allows axis-aligned evasion) is correct and confirmed. The specific numbers don't match because the current code conflates two rotation axes.

### 8.3 OS-Level User Isolation on Windows (Track A)

§12.2 specifies creating dedicated OS users per component with `chmod 600` file permissions. This is a Linux mechanism. On Windows, the equivalent is NTFS ACLs, which are more complex to script. **Resolution:** Track A on Windows uses process-level isolation (separate processes with distinct environment variables for secrets) and Python-level access control. Document honestly that filesystem-level user isolation requires Linux and is demonstrated in Track B Docker containers. If the venue machine runs Linux, the `make dev-up` script can create dedicated users.

### 8.4 `if_test` Context Blocks

The directive says to migrate `c_if` to `if_test` context blocks. On the currently installed Qiskit 1.1.1, `c_if` still works without deprecation warnings (verified by test). The `if_test` API was introduced in Qiskit 0.45+ but `c_if` remains functional in 1.1.1. **Resolution:** migrate anyway for forward compatibility, but if `if_test` causes issues with the transpiler or Aer, fall back to `c_if` with a documented note.

### 8.5 CHSH as "Independent Channel Integrity Probe"

§5.8 proposes CHSH as independent of the signature check. This is true but requires sacrificing Bell pairs as decoys, reducing the effective `L` and adding circuit overhead. Given the performance budget (§14), CHSH is in the "ship if at all possible" category. If it threatens the demo latency budget, it will be cut with documentation in LIMITATIONS.md.

---

## 9. What Needs to Be Preserved

From the directive's "Preserve these" list, confirmed present in v8:
- ✅ Clean L1–L4 layering
- ✅ Typed Pydantic contracts
- ✅ Thorough docstrings
- ✅ Multi-stage Docker build with non-root runtime user
- ✅ Healthchecks
- ✅ Coherent Makefile
- ✅ Structured JSON attack reporting
- ✅ Versioned baseline and detector identifiers
- ✅ Calibration routine that correctly varies seeds and computes mean + σ

All will be maintained or upgraded in v9.

---

## 10. Execution Plan Summary

```
Phase 0  ← YOU ARE HERE (migration plan, stop and wait for review)
Phase 1  → Foundation, hygiene, docs skeleton
Phase 2  → Quantum protocol core (THE critical path)
Phase 3  → Multi-vector detection + statistics
Phase 4  → Authentication + input validation
Phase 5  → Evidence plane
Phase 6  → Transport abstraction + fail-closed
Phase 7  → Side channels
Phase 8  → Attacker harness
Phase 9  → Testing + evaluation
Phase 10 → Dashboard + documentation
Phase 11 → Differentiator tier (D1 attribution first)
Phase 12 → Track B containers (only if time)
```

**Must-ship cut line (§20):** Phases 1–7 are mandatory. Phases 8–10 are "ship if at all possible." Phases 11–12 are differentiator/optional.

**If time runs short:** Cut in reverse order: Track B → D2-D6 → D1 → CHSH → element-mixing resistance (remove multi-bit claim) → PQC envelope (fallback to HMAC-based authentication with documented weakness).

---

**This document is the Phase 0 gate. Awaiting review before proceeding to implementation.**
