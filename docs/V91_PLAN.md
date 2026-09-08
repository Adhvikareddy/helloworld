# Q-SENTINEL v9.1 — Phase 0: Verification & Implementation Plan

**Branch:** `v9`, commit `54f4064`
**Date:** 2026-09-08
**Status:** Awaiting review before execution

---

## 1. Defect Verification (V1–V21)

Every item below was verified by reading the codebase at commit `54f4064`. File paths and line numbers are exact.

### V1 — CRITICAL · CONFIRMED ✅
**The adversary declares its own attack.**

- `verify.py:44`: `x_testbed_disturbance: float = Header(0.0, ge=0.0, le=1.0)` — HTTP header directly controls disturbance.
- `verify.py:102`: `TeleportationQDS(disturbance_prob=x_testbed_disturbance)` — passed straight into circuit construction.
- `verify.py:109`: `disturbance=x_testbed_disturbance` — also passed to `execute_session`.
- `teleportation_qds.py:64-65`: `if pure_x_rotation and disturbance > 0.0: qc.rx(disturbance * 3.14159, qr[2])` — non-monotonic: `rx(p·π)` wraps at π, explaining the V1 table (0.5→0.579, 1.0→0.5).
- `noise.py:36`: `p_depol = dist * 0.75` — depolarizing error applies to *all* 1-qubit gates (line 40), not just the channel qubit, which makes the noise model incoherent.

The attacker sets header to 0.0 and passes clean. The entire detection layer is bypassable.

### V2 — CRITICAL · CONFIRMED ✅
**Attack type selected by a client string.**

- `verify.py:105`: `pure_x = req.experiment_id == "test_pure_x_rotation"` — free-text field controls code path.
- `adaptive_x.py:17`: `payload["experiment_id"] = "test_pure_x_rotation"` — the attacker scenario triggers it by name.

### V3 — CRITICAL · CONFIRMED ✅
**No forgery attack surface exists.**

- `verify.py:99`: `alice_keys = global_keyvault.reveal_keys(req.session_id, req.signer_id, req.message_bit)` — server reveals keys internally.
- `verify.py:107-110`: `bob_outcomes, metadata = qds_core.execute_session(alice_keys, req.measurement_bases, ...)` — outcomes computed from those same server-held keys.
- The client cannot submit wrong key elements because no field for `revealed_keys` exists in `VerifyRequest` (lines 19-31).
- `scenarios.py:69-83`: The acknowledged workaround: `return payload, {"x_testbed_disturbance": 1.0} # Force max error to simulate totally wrong states`.

Forgery — the PS's primary threat — is structurally inexpressible.

### V4 — CRITICAL · CONFIRMED ✅
**The attack harness cannot load.**

- `attacker/scenarios.py` exists as a file (114 lines, defines `AttackerHarness`).
- `attacker/scenarios/` exists as a package directory with `__init__.py` (0 bytes).
- `runner.py:10`: `from attacker.scenarios import AttackerHarness` — Python resolves the package directory, not the module file. Result: `ImportError`.

All v9 attack scenarios in `scenarios.py` are unreachable.

### V5 — CRITICAL · CONFIRMED ✅
**Signer private keys committed to the repository.**

```
$ git ls-files "attacker/credentials/"
attacker/credentials/alice_sk.bin
attacker/credentials/bob_sk.bin
attacker/credentials/charlie_sk.bin
attacker/credentials/mallory_sk.bin
attacker/credentials/public_registry.json
```

- All four `*_sk.bin` files are 4032 bytes (ML-DSA-65 private key size) and tracked by git.
- `scenarios.py:24-25`: `with open("attacker/credentials/alice_sk.bin", "rb") as f: self.alice_sk = f.read()` — the harness holds Alice's private key.
- `scenarios.py:57`: `sig = PQCEnvelope.sign_payload(self.alice_sk, payload)` — used to sign as Alice in "attack" scenarios.
- `.gitignore` has no entry for `attacker/credentials/` or `*_sk.bin`.

### V6 — HIGH · CONFIRMED ✅
**v8's fatal code path survives.**

- `teleportation_qds.py:148`: `def execute_verification(self, shots: int = 1024, disturbance_prob: float = 0.0, is_invalid_signature: bool = False)`.
- `teleportation_qds.py:158`: `if is_invalid_signature:` short-circuits and returns `protocol_valid: False` without running any circuit.
- `test_l1.py:125,132`: Tests for `is_invalid_signature=True/False` still present.
- `attacker/scenarios/forgery.py:43`: `payload["is_invalid_signature"] = True` — targets a field that `VerifyRequest` does not declare (line 19-31 of verify.py), so the old attack suite is broken.

### V7 — HIGH · CONFIRMED ✅
**Analytical thresholds computed but never used.**

- `analytical.py:10`: `def derive_thresholds(...)` is defined.
- Grep for `derive_thresholds` across the repo returns only the definition itself — **zero call sites**.
- `thresholds.json`: `{"tau_low": 0.05, "tau_high": 0.15, "version": "cal-v9-initial"}`.
- `policy.py:13-14`: `self.tau_low = 0.05; self.tau_high = 0.15` — byte-identical hardcoded defaults.

The analytical derivation is dead code. The deployed thresholds are magic numbers.

### V8 — HIGH · CONFIRMED ✅
**No distribution phase, so no stored verifier records.**

- The only endpoint is `POST /v1/qds/verify`. There is no `distribute` endpoint.
- `verify.py:99-110`: Keys are revealed and quantum circuits are executed in the *same request*. There is no temporal separation.
- `measurement_bases` arrives from the client at verify time (`verify.py:27`).
- Nothing is stored per-verifier. Non-repudiation is asserted rather than realised.

### V9 — HIGH · CONFIRMED ✅
**Hard 2-second latency floor.**

- `verify.py:154-156`: `target_latency = 2.0; if elapsed < target_latency: time.sleep(target_latency - elapsed)`.
- `verify.py:174`: `latency = (time.time() - start_time) * 1000` — measured *after* the sleep, so always ≈2000ms.

### V10 — HIGH · CONFIRMED ✅
**Response tiering trusts a self-declared entitlement.**

- `verify.py:162`: `if decision != "REJECT" or req.verifier_id in ["auditor", "admin"]:`.
- `verifier_id` is a client-supplied string in `VerifyRequest` (line 22). Any caller can set `verifier_id="admin"` to receive full findings on REJECT.

### V11 — MEDIUM · CONFIRMED ✅
**No honest noise floor in the live path.**

- `noise.py:23-24`: `if disturbance_prob <= 0.0: return noise_model` — returns an empty noise model.
- When `x_testbed_disturbance=0.0` (default), the simulator runs on an ideal channel, yielding m̂ = 0.0 exactly.
- Thresholds are degenerate: `tau_low=0.05` is infinitely far from 0.0. No legitimate traffic touches the noise floor.

### V12 — MEDIUM · CONFIRMED ✅
**No generated evidence.**

- `experiments/results/` does not exist (`Test-Path` returns `False`).
- `.gitignore:19`: `experiments/results/` is gitignored, but it was also never created.
- `experiments/forgery_curve.py`, `multi_vector_matrix.py`, `optimal_adversary_experiment.py` exist as scripts but have never been run with committed output.

### V13 — MEDIUM · CONFIRMED ✅
**Test coverage is thin where it matters.**

- `tests/integration/`: 1 file (`test_api.py`).
- `tests/property/`: 1 file (`test_qds_properties.py`).
- `tests/unit/`: 5 files.
- Absent: forgery-by-verifier, key reuse across restart, adaptive-X detection, composite multi-vector, probe-crash fail-closed, ledger concurrency/truncation, timing non-separability, repudiation, distribution response leak, experiment_id behavioural equivalence, git-tracked credential check, AI/ML compliance grep.

### V14 — MEDIUM · CONFIRMED ✅
**Verifier authorisation is a name check.**

- `identity.py:24-25`: `def is_verifier_authorized(self, name: str) -> bool: return name in self.authorized_verifiers`.
- Registration at line 15-19 stores by name. No cryptographic proof the caller controls that identity.

### V15 — MEDIUM · CONFIRMED ✅
**Keyvault is an in-memory global.**

- `keyvault/__init__.py:92`: `global_keyvault = KeyVault()`.
- `keyvault/__init__.py:33-35`: `self._sessions: Dict[str, KeySession] = {}; self._used_sessions: Set[str] = set()` — both in-memory.
- Comment at line 34: "Track used session IDs globally to prevent reuse across restarts if backed by DB" — but no DB backing exists.
- Key reuse protection is lost on process restart or with multiple workers.

**Note:** The nonce guard (`nonce.py`) IS SQLite-backed, so replay protection survives restart. But the keyvault single-use check does not.

### V16 — MEDIUM · CONFIRMED ✅
**Single-bit messages only.**

- `key_material.py:47-61`: `generate_key_set(L)` produces `(k_0, k_1)` — one key pair for message bits 0 and 1.
- `LIMITATIONS.md`: 16 lines. Does not mention the single-bit constraint.
- `README.md:166`: "P_forge ≤ 10⁻⁶ at L=300" — implies arbitrary messages.

### V17 — MEDIUM · CONFIRMED ✅
**Security documentation is thin.**

- `SECURITY_ANALYSIS.md`: 60 lines. No who-knows-what-when table, no ε-unforgeability/ε-non-repudiation definitions, no side-channel analysis.
- `docs/IMPACT_AND_DEPLOYMENT.md` does not exist.

### V18 — LOW · CONFIRMED ✅
**Environment inconsistency.**

- `V9_MIGRATION_PLAN.md:181`: `Python | 3.14.0 (system; directive specifies 3.11 — see note below)`.
- `V9_MIGRATION_PLAN.md:186`: "This is acceptable because all libraries function identically on both versions" — unverified assertion.
- `requirements.txt:12`: `qiskit==1.1.1` — released before Python 3.14.

### V19 — LOW · CONFIRMED ✅
**Single commit.**

```
$ git log --oneline -20
54f4064 new
fbab49a Refined
186b36b initial commit
```

The v9 branch has one new commit titled "new" (the other two are from earlier branches).

### V20 — CONFIRMED ✅ (with caveat)
**Portal items not addressed.**

- **Dataset Link**: `https://drive.google.com/drive/folders/1rgGdaPn9rdGZfkaqc3MKVfdCK8r5X_gk` — I attempted to fetch this. The page title resolves to "Egreen Quanta - Google Drive", but the actual folder contents require Google authentication and are not accessible programmatically. **This is an open risk.**
- **Delivery Table**: Not referenced anywhere in the repository. No `docs/DELIVERABLES.md` exists.

### V21 — CONFIRMED ✅
**Missing deliverables.**

- No `experiments/concurrent_campaign.py` (grep returns only a reference in `V9_MIGRATION_PLAN.md:525`).
- No CHSH entanglement verification anywhere.
- No dispute-resolution protocol beyond the description in `SECURITY_ANALYSIS.md:56-59`.
- Track A filesystem permission proofs are described in the migration plan as simulated, not executed.

---

## 2. §3 Endpoint Contracts & Storage Schema

### 2.1 Storage Schema (SQLite)

A new database `data/qds_sessions.db` with three tables:

```sql
-- Distribution records: one row per (session, verifier, position)
CREATE TABLE distribution_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    signer_id TEXT NOT NULL,
    verifier_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    message_bit INTEGER NOT NULL,
    basis_chosen TEXT NOT NULL,          -- verifier's CSPRNG-chosen basis: 'X', 'Y', or 'Z'
    outcome INTEGER NOT NULL,           -- measurement outcome: 0 or 1
    created_at REAL NOT NULL,
    UNIQUE(session_id, verifier_id, position)
);

CREATE INDEX idx_session_verifier ON distribution_records(session_id, verifier_id);

-- Session metadata: one row per distribution session
CREATE TABLE distribution_sessions (
    session_id TEXT PRIMARY KEY,
    signer_id TEXT NOT NULL,
    L INTEGER NOT NULL,
    message_bit INTEGER NOT NULL,
    nonce TEXT NOT NULL,
    channel_type TEXT NOT NULL DEFAULT 'none',
    channel_magnitude REAL NOT NULL DEFAULT 0.0,
    created_at REAL NOT NULL,
    ledger_event_id TEXT
);

-- Verification consumption tracking: one row per (session, verifier)
CREATE TABLE verification_consumed (
    session_id TEXT NOT NULL,
    verifier_id TEXT NOT NULL,
    consumed_at REAL NOT NULL,
    decision TEXT NOT NULL,
    PRIMARY KEY (session_id, verifier_id)
);
```

### 2.2 `POST /v1/qds/distribute` — New Endpoint

**Request schema:**
```python
class DistributeRequest(BaseModel):
    signer_id: str = Field(..., max_length=64)
    verifier_ids: List[str] = Field(..., min_length=2, max_length=10)
    L: int = Field(..., ge=30, le=10000, description="Security parameter")
    message_bit: int = Field(..., ge=0, le=1)
    nonce: str = Field(..., max_length=128)
    timestamp: float
    signature: str = Field(..., max_length=8192)  # ML-DSA-65 sig
```

**Server behaviour:**
1. Authenticate signer via PQC identity.
2. Validate nonce freshness and timestamp.
3. Generate `k_0` and `k_1` via keyvault (`generate_key_set(L)`). Select `k = k_{message_bit}`.
4. **For each verifier independently:**
   - Choose `L` measurement bases server-side via `secrets.choice(['X', 'Y', 'Z'])` — one per position.
   - Build and execute `L` teleportation circuits: prepare `k[i]` state, apply channel conditions (from server-side testbed config), measure in `basis_chosen[i]`.
   - Store `(session_id, verifier_id, position, message_bit, basis_chosen, outcome)` into SQLite.
5. Record distribution event in the ledger.
6. Derive expected matched-subset size as `≈ L/3` per verifier.

**Response schema:**
```python
class DistributeResponse(BaseModel):
    session_id: str
    L: int
    expected_matched_subset: int
    evidence_id: str
    # MUST NOT contain: keys, bases, outcomes
```

**Test assertion:** Response body does not contain any field named `keys`, `bases`, `outcomes`, `k_0`, `k_1`, or `revealed_keys`.

### 2.3 `POST /v1/qds/verify` — Rewritten Endpoint

**Request schema (changes from v9):**
```python
class VerifyRequest(BaseModel):
    session_id: str = Field(..., max_length=128)
    signer_id: str = Field(..., max_length=64)
    verifier_id: str = Field(..., max_length=64)
    nonce: str = Field(..., max_length=128)
    timestamp: float
    message_bit: int = Field(..., ge=0, le=1)
    # NEW: client-supplied signature (the revealed key set)
    revealed_keys: List[QuantumKeyElementSchema] = Field(
        ..., max_length=10000,
        description="The revealed key elements — this IS the signature"
    )
    signature: str = Field(..., max_length=8192)  # PQC envelope
    experiment_id: Optional[str] = Field(None, max_length=64)  # opaque label only

    # REMOVED: measurement_bases (now from stored records)
    # REMOVED: x_testbed_disturbance header (V1 fix)
    # No code may branch on experiment_id value (V2 fix)
```

Where:
```python
class QuantumKeyElementSchema(BaseModel):
    basis: str = Field(..., pattern="^[XYZ]$")
    bit: int = Field(..., ge=0, le=1)
```

**Server behaviour:**
1. Load stored records for `(session_id, verifier_id)` from SQLite. If absent → REJECT with finding `session_not_distributed`.
2. Check single-use: if `(session_id, verifier_id)` is in `verification_consumed` → REJECT with finding `session_already_consumed`.
3. Validate `len(revealed_keys) == L` from session metadata.
4. Compute matched subset: positions where `revealed_keys[i].basis == stored_basis_chosen[i]`.
5. Compute m̂ over matched subset: count positions where `revealed_keys[i].bit != stored_outcome[i]`.
6. Feed `StatisticalProbe` and `TomographyProbe` with the stored bases, revealed keys, and stored outcomes.
7. **Run no quantum circuits.** Verification is purely classical comparison.
8. Mark `(session_id, verifier_id)` as consumed in `verification_consumed`.
9. Enforce dual-threshold: `s_a` for acceptance, `s_v` (looser) for transferability.

**Legitimate flow:**
- Alice calls keyvault reveal to get her real keys, submits them as `revealed_keys`.
- Bases match at ≈L/3 positions. On matched positions, bits agree (modulo channel noise) → m̂ ≈ `e_honest` → ACCEPT.

**Forgery flow:**
- Mallory guesses key elements uniformly. On matched positions (≈L/3), she guesses correct bit with probability `p_opt ≈ 0.7887` → m̂ ≈ `1 - p_opt ≈ 0.211` → well above `s_a` → REJECT.

### 2.4 `POST /v1/testbed/channel` — New Operator Endpoint

**Request:**
```python
class ChannelConfigRequest(BaseModel):
    channel_type: str = Field(..., pattern="^(none|rx_only|rz_only|depolarizing|intercept_resend)$")
    magnitude: float = Field(..., ge=0.0, le=1.0)
    operator_signature: str  # Must be from operator credentials, NOT signer/verifier/attacker
```

**Behaviour:** Sets server-side testbed channel state. Only affects subsequent `distribute` calls. Requires operator credentials distinct from any participant. Refuses when `JURY_MODE=strict` unless explicitly enabled. Every change is ledger-recorded.

### 2.5 `POST /v1/qds/reveal` — Signer Key Retrieval (Implied by §3)

Alice needs to obtain her keys client-side to submit as `revealed_keys`. This endpoint is implied by the directive's "Alice fetches her real keys via an authenticated keyvault reveal."

**Request:**
```python
class RevealRequest(BaseModel):
    session_id: str
    signer_id: str
    message_bit: int = Field(..., ge=0, le=1)
    signature: str  # PQC envelope authenticating the signer
```

**Behaviour:** Returns the key set for `message_bit`. Marks keys as revealed (separate from session consumption). Only the authenticated signer can call this. Returns 403 if `signer_id` doesn't match the session's signer.

### 2.6 Dual-Threshold Transferability Rule

```
s_a < s_v
```

- **Verifier accepts** if m̂ ≤ s_a (strict threshold).
- **Transferability holds** if any verifier who accepts guarantees m̂ ≤ s_v at any other verifier.
- Both derived from `derive_thresholds` with different α values.
- Disagreement (one verifier accepts, another rejects) is itself a finding recorded in the ledger.

---

## 3. Open Items

### 3.1 Dataset Link — INACCESSIBLE ⚠️

The Dataset Link (`https://drive.google.com/drive/folders/1rgGdaPn9rdGZfkaqc3MKVfdCK8r5X_gk`, titled "Egreen Quanta") requires Google authentication. The page rendered but did not expose folder contents to unauthenticated HTTP requests.

**Recommendation:** The team should manually download the folder contents and share them. If the folder contains reference parameters, a protocol variant, or evaluation criteria, they could change the design. **This is an open risk that should be resolved before §3 implementation if possible.**

### 3.2 Delivery Table — NOT RETRIEVED ⚠️

The SIH portal's Delivery Table (Expected Deliverables) is not accessible programmatically and is not referenced anywhere in the repository. The team must retrieve this manually from the SIH portal and provide it so I can create `docs/DELIVERABLES.md` mapping every row to a repository artifact.

### 3.3 §3.3 Confirmation — Forgery-by-Verifier ✅

**I have read §3.3 and confirm understanding.**

The key insight: Bob holds his own `(basis_chosen, outcome)` records. He can fabricate a key set that perfectly matches his own records → m̂ = 0 against Bob. **This is not a bug** — it is a fundamental property of single-verifier schemes.

What defeats Bob is Charlie:
- Charlie's bases were chosen independently (CSPRNG, server-side).
- Bob has never seen Charlie's bases.
- Bob's fabricated key set matches Charlie's basis at ≈1/3 positions, and on those, Bob's fabricated bit is correct by chance → m̂ ≈ 0.5 against Charlie → REJECT.

Therefore:
- `forgery_by_verifier` test: Bob fabricates from his records, submits as `verifier_id="charlie"` → **REJECT**.
- Not: Bob verifying against Bob (which would pass and is expected to).
- The dual-threshold rule `s_a < s_v` formalises this: what one verifier accepts must remain acceptable to another at the looser `s_v`.

---

## 4. Feasibility Assessment & Objections

### 4.1 Nothing infeasible identified

All requirements in the directive are implementable with the existing technology stack (FastAPI, SQLite, Qiskit-Aer, scipy, pqcrypto). No requirement exceeds what the codebase already partially implements.

### 4.2 Minor design notes

1. **Keyvault reveal for legitimate flow:** The directive says "Alice fetches her real keys via an authenticated keyvault reveal." This implies a `POST /v1/qds/reveal` endpoint (§2.5 above) not explicitly listed in the directive. I will implement it as it's necessary for the flow to work.

2. **Channel model monotonicity:** The current `rx(p·π)` wraps due to unitary periodicity (Rx(π) = -iX, Rx(2π) = -I). For coherent attacks, the principled model: `rx(θ)` where θ is the rotation angle (0 to π), magnitude maps linearly. For depolarizing: `depolarizing_error(p, 1)` applied specifically to the channel qubit, not all gates (the current approach at `noise.py:40` applies to all single-qubit gates, which is incoherent). I will verify monotonicity by sweeping θ and plotting m̂ vs θ.

3. **Single-bit vs. multi-bit:** Given time constraints and the directive's cut-line guidance, I propose stating the single-bit limitation honestly in `README.md`, `LIMITATIONS.md`, and the demo script, rather than implementing multi-bit. Multi-bit is on the cut list.

4. **`experiments/results/` is gitignored:** `.gitignore:19` excludes `experiments/results/`. This line must be removed or results won't be committed.

### 4.3 One minor correction to the directive

The directive states at V7: "byte-identical to v8's hardcoded values at `policy.py:19-20`". In v9, the hardcoded values are at `policy.py:13-14`, not 19-20. The defect description is otherwise entirely accurate.

---

## 5. Execution Order

Per the directive's §12:

| Phase | Section | Description | Dependencies |
|-------|---------|-------------|--------------|
| 1 | §3 | Split distribution from verification | None — centre of the work |
| 2 | §5, §6 | Repair harness, credential hygiene | §3 (new endpoints to target) |
| 3 | §4 | Relocate channel adversary | §3 (channel applies at distribute) |
| 4 | §7 | Wire thresholds, p-values, FWER | §3 (needs real m̂ data) |
| 5 | §8 | Latency & side channels | §3 (verification is now classical) |
| 6 | §9 | Remaining wiring (persist keyvault, nonces, verifier auth) | §3, §7 |
| 7 | §10 | Evidence generation | §3–§7 (needs working system) |
| 8 | §11 | Tests, docs, portal items | All above |

**Cut-line:** Must ship: §3, §5, §6, §7's threshold wiring, §4. Ship if possible: §10's forgery curve + adaptive-X, §8, §9, §11's docs. Cut last: multi-bit, CHSH, dispute resolution beyond dual threshold, `concurrent_campaign`.

---

## 6. Summary

All 21 defects are confirmed against the code as described. The critical path is clear:

1. **V1+V2+V3+V8** are all fixed by §3 (distribution/verification split).
2. **V4+V5+V6** are fixed by §5+§6 (harness repair + credential hygiene).
3. **V7** is fixed by §7 (wire analytical thresholds).
4. **V9+V10** are fixed by §8 (latency + entitlement).
5. **V11** is fixed by §3+§4 (honest noise in distribution channel).
6. **V12–V21** are addressed by §9–§11.

**Awaiting approval to proceed with Phase 1 (§3: structural split).**
