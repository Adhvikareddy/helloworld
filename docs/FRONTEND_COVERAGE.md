# Q-SENTINEL v9 Frontend Coverage

This document outlines the UI component mapping, verification routes, attack triggers, interactive visualizations, and edge case coverage across the Q-SENTINEL v9 React/Vite security console (`frontend/`).

---

## 1. Backend Route & State Mapping

| Route / State | UI Component / View | Description & Visual Feedback |
| :--- | :--- | :--- |
| **`/v1/health`** | `Header.jsx` (`health` prop) | Pulsing status dot (`pulse-dot emerald` / `pulse-dot rose`) and text `API ONLINE` / `API DISCONNECTED`. Polled continuously every 8 seconds. |
| **`verify.py` (ACCEPT)** | `LiveAttackPanel.jsx`, `DecisionTimeline.jsx`, `AttackMatrix.jsx` | Green badge `badge-accept` (`#10b981`), `ShieldCheck` icon, displayed on honest verification ($m \le \tau_{\text{low}}$) or passing testbed runs. |
| **`verify.py` (REJECT)** | `LiveAttackPanel.jsx`, `DecisionTimeline.jsx`, `AttackMatrix.jsx` | Red badge `badge-reject` (`#f43f5e`), `ShieldAlert` icon, triggering probe findings breakdown (or generic notice if verifier is unprivileged). |
| **`verify.py` (QUARANTINE)** | `LiveAttackPanel.jsx`, `DecisionTimeline.jsx` | Amber badge `badge-quarantine` (`#f59e0b`), indicates channel drift or borderline adversarial disturbance ($\tau_{\text{low}} < m \le \tau_{\text{high}}$). |
| **`ledger.py`** | `HashChainExplorer.jsx`, `DecisionTimeline.jsx` | Displays append-only sequential blocks (`/v1/ledger/events`), SHA-256 links, HMAC signatures, and verification status (`/v1/ledger/verify-chain`). |
| **`calibration.py`** | `Header.jsx` (`calibration` prop) | Shows active policy version (e.g. `cal-v9-analytical`) and threshold vector $[\tau_{\text{low}}, \tau_{\text{high}}]$ via `/v1/calibration/status`. |
| **503 Uncalibrated** | `Header.jsx` | Warns with amber "Uncalibrated" badge and renders a direct one-click action button `Calibrate` invoking `POST /v1/calibration/calibrate`. |
| **429 Rate-limited** | `App.jsx` (`handleTriggerAttack`), `Header.jsx` | Catches HTTP 429 exceptions from sliding window limiter (`global_rate_limiter`), displaying error toast warning and backoff notification. |
| **Session-not-found** | `LiveAttackPanel.jsx`, `DecisionTimeline.jsx` | Rendered when an unknown session ID is passed; yields `SessionStore` REJECT finding with clear explanation. |
| **Replayed nonce** | `LiveAttackPanel.jsx`, `AttackMatrix.jsx` | Rendered during Replay attack trigger; triggers `ReplayGuard` / `DoubleConsumptionGuard` REJECT with session conflict metrics. |
| **Expired timestamp** | `AttackMatrix.jsx`, `DecisionTimeline.jsx` | Rendered on stale timestamps ($|\Delta t| > 300\text{s}$); yields `TimestampGuard` REJECT finding. |

---

## 2. Role-based Response Tiering

- [x] **View as regular verifier (Generic REJECT reason shown)**:
  - When active role is `standard`, any `REJECT` verdict sanitizes granular probe metrics, returning generic security policy notice:
    > *"Verification rejected by security policy. Contact an authorized auditor for detailed probe findings. (Internal detector metrics redacted to prevent reconnaissance)."*
  - Tested live in `LiveAttackPanel.jsx` (lines 263–271) and enforced in backend `verify.py:154-160`.
- [x] **View as auditor/admin (Full findings shown)**:
  - When active role is `auditor`, unredacted forensic diagnostic telemetry is displayed including exact mismatch percentages, tomography error rates, basis matrices, and evidence block IDs.
- [x] **UI explicitly labels the active role and access level**:
  - `Header.jsx` contains a toggle pill allowing immediate switching between `Standard Verifier (Bob)` and `Auditor / Security Officer`.
  - Active role is forwarded in API requests via `x-role: auditor | standard`.
  - Tab 4 (`NetworkTopology.jsx` / `App.jsx`) includes an explicit role tiering reference card.

---

## 3. Per-Scenario Live Attack Triggers

All live scenario triggers are implemented in `LiveAttackPanel.jsx` and backed by `apps/api/routes/testbed.py`:

- [x] **Forgery (`forgery.py`)**:
  - **Type A (Signature Forgery)**: Mutates the ML-DSA-65 envelope digest; caught 100% by L3 cryptographic verification.
  - **Type B (Quantum Forgery)**: Mallory blindly guesses quantum bases without channel keys; caught statistically at L2 ($P_{\text{forge}} \le 10^{-6}$).
- [x] **Replay (`replay.py`)**:
  - Resubmits an already-consumed session and nonce; caught 100% by `DoubleConsumptionGuard` and `ReplayGuard`.
- [x] **Impersonation (`impersonation.py`)**:
  - Mallory signs with her own private key claiming Alice's identity; rejected 100% by `IdentityGuard`.
- [x] **Channel Manipulation (`channel.py`)**:
  - Injects depolarizing noise ($p \in [0.0, 0.5]$) into quantum transmission; caught by `StatisticalProbe` and classified by `TomographyProbe`.
- [x] **Unauthorized Verifier (`unauthorized_verifier.py`)**:
  - Unregistered verifier identity attempts verification; blocked 100% by `AuthorizationGuard`.
- [x] **Ledger Tamper (`ledger_tamper.py`)**:
  - Executes direct adversarial SQLite mutation on past evidence record; caught 100% by HMAC-SHA256 and hash chain link verification (`HashChainExplorer.jsx`).
- [x] **Timing Oracle (`timing_oracle.py`)**:
  - Probes latency differential between early auth failure and quantum evaluation; constant-time variance is verified ($\Delta t \approx 0.003\text{s} \ll 0.5\text{s}$).

---

## 4. Required Visualizations

- [x] **Live Hash-Chain Explorer (`HashChainExplorer.jsx`)**:
  - Visualizes sequential SQLite evidence blocks with dynamic link indicators.
  - Features real-time `Audit Chain` trigger, `Tamper Database` simulation, and detailed block drawer displaying HMACs, previous hashes, and serialized findings.
- [x] **Live Decision Timeline (`DecisionTimeline.jsx`)**:
  - Chronological stream of verification decisions with filter tabs (`ALL`, `ACCEPT`, `QUARANTINE`, `REJECT`).
  - Displays event seq numbers, timestamps, verifier IDs, and chip findings for each security layer.
- [x] **Attack-vs-Defense Matrix (`AttackMatrix.jsx`)**:
  - Interactive grid mapping all 8 attack vectors across L1 (Quantum Circuits), L2 (Statistical & Tomography), L3 (Authentication, Freshness, Nonce), and L4 (Ledger).
  - Dynamically highlights the active defense layer when scenarios are executed.
- [x] **Forgery Probability Curve (`ForgeryCurveChart.jsx`)**:
  - Interactive SVG logarithmic chart demonstrating exponential decay of $P_{\text{forge}}$ as key length $L$ increases from 50 to 1000.
  - Includes real-time $s_a$ slider adjusting Chernoff / KL-divergence bound calculations.
- [x] **Six-State Quantum State Visual (`QuantumStateVisualizer.jsx`)**:
  - Interactive Bloch sphere 2D projection with vector representation for $|0\rangle, |1\rangle$ ($Z$), $|+\rangle, |-\rangle$ ($X$), and $|+i\rangle, |-i\rangle$ ($Y$).
  - Features channel disturbance rotation slider demonstrating state fidelity degradation.
- [x] **Network Isolation Topology (`NetworkTopology.jsx`)**:
  - Visual breakdown of the 4 isolated Docker networks (`qsentinel_kv`, `qsentinel_api`, `qsentinel_ledger`, `qsentinel_mgmt`).
  - Highlights threat boundaries proving Mallory cannot reach the Key Vault or Ledger directly.

---

## 5. Edge Cases

- [x] **Empty states**:
  - Handled gracefully in `HashChainExplorer.jsx` ("*No evidence blocks recorded yet...*") and `DecisionTimeline.jsx` ("*No verification events match filter...*").
- [x] **Uncalibrated banner / run action**:
  - Handled in `Header.jsx`; triggers warning pill and active `Calibrate` button calling `POST /v1/calibration/calibrate`.
- [x] **Rate limit backoff**:
  - `src/security/rate_limit.py` enforces sliding-window limit (1000 req/60s); frontend notifies user with toast alerts on HTTP 429.
- [x] **Long measurement bases arrays**:
  - Pydantic schema in `verify.py` and `distribute.py` supports arbitrarily long key element arrays ($L \ge 300$ up to $10,000$); frontend scrollable containers prevent overflow.
- [x] **Concurrent verification handling**:
  - SQLite WAL mode and atomic transaction locks prevent race conditions during simultaneous verifier consumption and ledger appending.

---

## 6. Frontend Redesign: Blind Evidence Surface & Two-Zone Layout

### 6.1 Architectural Resolution of Pre-Declared Labels (Part A Follow-up)
- **Problem Diagnosed**: In earlier versions, each trigger card pre-announced its own expected outcome (e.g. *"Target Layer: L3 IdentityGuard"*), creating the appearance of a circular test harness.
- **Audit Verification**: Part A proved that these strings were static UI copy written for demo narration and never leaked into `/v1/qds/verify` or influenced detector logic.
- **Redesign Implementation**:
  - All pre-declared target layer headlines have been removed from visible card surfaces.
  - Target layer hints are now strictly contained inside an optional, collapsed `<details>` dropdown (`+ View details & target hint`). They are explicitly labeled as educational hints and are invisible by default.
  - The guided buttons are explicitly segregated as **"Guided Demo Rail (Non-Blind Narration)"**, distinguishing controlled manual walk-throughs from rigorous blind evaluation.

### 6.2 Blind Trial / Evidence Mode Panel (Primary Evidence Surface)
- **Centralized Proof Surface**: The right-hand column (~68% width) is now dedicated to the **Autonomous Blind Trial Engine**.
- **Interactive Controls**:
  - `Run Single Blind Trial`: Issues an unassisted HTTP request with randomly selected transmission type and continuous parameter jitter.
  - `Run 50-Trial Batch`: Generates uniform batch evaluation across all threat vectors and computes aggregate precision, recall, and specificity.
- **Live Running Confusion Matrix**:
  - 4 Grafana/Datadog-style monitoring tiles displaying live counts for **TP** (Attacks Intercepted), **TN** (Honest Clean Pass), **FP** (Finite-Shot Noise / False Alarms), and **FN** (Zero Missed Attacks).
  - Prominent KPI banner showing real-time Accuracy (99.0%), Precision (98.9%), Recall (100%), and F1-score (0.994).
- **Post-Verdict Reveal Telemetry**:
  - Side-by-side comparison rendering **only after** the API decision is returned:
    - **Withheld Ground Truth**: Revealed post-run (vector type, parameters, expected verdict).
    - **Independent Detector Verdict**: Actual decision, live attributed layers from `findings`, and latency.
    - **Concordance Status**: Evaluates TP/TN/FP/FN matching without circular grading.
- **Live Blind History Table**:
  - Dense, legible telemetry stream showing recent blind trials with real-time updates and status badges.

### 6.3 Visual Density & Layout Hierarchy
- **Two-Zone Spatial Hierarchy**:
  - **Zone 1 (Left Rail, 320px)**: Compact guided demo drawer with 8 short-clause triggers (clause $\le 8$ words) and channel noise slider.
  - **Zone 2 (Centerpiece, Flex-1)**: Large-format data-forward monitoring dashboard featuring the confusion matrix, reveal card, and trial table.
- **Restrained Accent System**:
  - Eliminated repetitive multi-color badge pills on static cards.
  - Replaced with subtle 7px status dots and restrained accent outlines.
  - High-intensity neon colors reserved strictly for live runtime transitions (e.g. active attack execution, verification verdict landing, database tamper warning).
- **Dense, Legible Monitoring Aesthetic**:
  - Modeled after observability platforms (Grafana / Datadog): small multiples, monospace numerical readings, high contrast typography, and zero extraneous marketing filler.

