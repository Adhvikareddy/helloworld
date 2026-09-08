# Q-SENTINEL API Contract Audit

This document audits all HTTP network interactions initiated by the React frontend (`frontend/src/`) against the FastAPI backend router endpoints.

Every call was extracted directly from source files (`grep` across `frontend/src/`) and verified against the live OpenAPI route table registered in `apps/api/main.py`.

---

## 1. Full Contract Mapping Table

| # | Frontend Call (Method + Path) | Triggering Component & File | Backend Route Target | Status | Implementation Details |
|---|-------------------------------|-----------------------------|----------------------|--------|------------------------|
| 1 | `GET /v1/health` | `App.jsx:42` (System health polling) | `GET /v1/health` | **Pre-existing** | Returns API status, version `v9.1`, and subcomponent readiness. |
| 2 | `GET /v1/calibration/status` | `App.jsx:46` (Dashboard header & policy monitor) | `GET /v1/calibration/status` | **Pre-existing** | Returns policy version, calibrated thresholds, and active detector parameters. |
| 3 | `POST /v1/calibration/calibrate` | `App.jsx:118` ("Calibrate Baseline" button) | `POST /v1/calibration/calibrate` | **Implemented (Phase 1)** | Genuinely runs Qiskit-Aer baseline simulation via `src/calibration/grid_search.py`, re-calibrates thresholds, writes `data/calibration/thresholds.json`, and reloads in-memory policy. |
| 4 | `GET /v1/ledger/events?limit=50` | `App.jsx:50` (Live decision timeline & hash chain explorer) | `GET /v1/ledger/events` | **Implemented (Phase 1)** | Performs real SQLite query against `evidence` table, returning up to $N$ recent verification events ordered newest first. |
| 5 | `GET /v1/ledger/verify-chain` | `App.jsx:57`, `App.jsx:139` ("Verify Chain Integrity" audit) | `GET /v1/ledger/verify-chain` | **Pre-existing** | Recomputes cryptographic HMAC-SHA256 hash chain over all records in SQLite database, reporting `chain_valid: true/false` and index if broken. |
| 6 | `POST /v1/ledger/tamper` | `App.jsx:160` ("Tamper DB Demo" judge button) | `POST /v1/ledger/tamper` | **Implemented (Phase 1)** | Direct SQLite record mutation on the most recent ledger row without updating the HMAC chain, enabling live proof of tamper detection. |
| 7 | `POST /v1/testbed/attack/{scenario}` | `App.jsx:86` (Per-scenario "Trigger Attack" cards) | `POST /v1/testbed/attack/{scenario_name}` | **Implemented (Phase 1)** | Genuine pipeline orchestration executing `/distribute` $\to$ `/reveal` $\to$ adversarial mutation $\to$ `/verify` through real multi-layer detection. Scenarios: `forgery`, `replay`, `impersonation`, `unauthorized`, `channel`, `ledger`. |
| 8 | `GET /v1/testbed/blind-history` | `LiveAttackPanel.jsx:133` (Trial history & empirical score panel) | `GET /v1/testbed/blind-history` | **Pre-existing** | Retrieves past blinded trial executions, computing empirical metrics (accuracy, F1, latency, layer distribution). |
| 9 | `POST /v1/testbed/blind-trial` | `LiveAttackPanel.jsx:148` ("Run Blind Trial" button) | `POST /v1/testbed/blind-trial` | **Pre-existing** | Runs single randomized blind evaluation trial through full `/distribute` $\to$ `/verify` pipeline. |
| 10 | `POST /v1/testbed/blind-batch` | `LiveAttackPanel.jsx:182` ("Run Blind Batch (10)" button) | `POST /v1/testbed/blind-batch` | **Pre-existing** | Executes batch of randomized blind trials (honest traffic, classical forgeries, quantum perturbations, replays, impersonations). |

---

## 2. Audit Summary

- **Total Frontend Network Call Sites**: 10
- **Pre-existing Backend Routes**: 6
- **Routes Implemented in Phase 1**: 4 (`/v1/testbed/attack/{scenario}`, `/v1/calibration/calibrate`, `/v1/ledger/tamper`, `/v1/ledger/events`)
- **Missing / 404 Routes**: **0** (Zero discrepancy)
- **Unused Backend Endpoints**:
  - `POST /v1/qds/distribute` (Used by backend orchestration & external CLI attacker)
  - `POST /v1/qds/reveal` (Used by backend orchestration & external CLI attacker)
  - `POST /v1/qds/verify` (Core protocol verification pipeline)
  - `GET /v1/ledger/verify/{event_id}` (Single-event ledger lookup)
  - `POST /v1/calibration/reload` (Manual policy reload)

All frontend interactions map 1-to-1 to verified, functional backend endpoints.
