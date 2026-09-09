# Q-SENTINEL: Deliverables & Compliance Matrix
## Smart India Hackathon (SIH) Problem Statement 26141
**Theme:** Blockchain & Cybersecurity  
**Sub-Theme:** Quantum-Inspired Cyber Threat Detection for Digital Signature Security & Immutable Evidence Chains

---

## Executive Summary

Q-SENTINEL addresses SIH PS 26141 by combining **NIST Post-Quantum Cryptography (ML-DSA-65)**, **Quantum Digital Signatures (QDS)** via simulated quantum teleportation and matched-basis measurement, a **four-layer real-time cyber threat detection engine**, and an **immutable HMAC-SHA256 hash-chained evidence ledger**.

This document maps every requirement in the SIH PS 26141 Delivery Table directly to the concrete code modules, API endpoints, test suites, and empirical evidence artifacts in this repository.

---

## SIH Expected Deliverables Mapping Table

| # | Expected Deliverable (SIH PS 26141) | Repository Implementation | Target Artifacts & Code Links | Verification Evidence | Status |
|---|---|---|---|---|:---:|
| **D1** | **Post-Quantum Digital Signature Verification**<br>Quantum-resistant cryptographic envelope providing authentication against quantum algorithmic attacks (Shor's, Grover's). | Hybrid quantum-classical cryptographic envelope implementing NIST FIPS 204 ML-DSA-65 (CRYSTALS-Dilithium). Validates request signatures and binds signer identity. | [`src/security/envelope.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/security/envelope.py)<br>[`src/security/identity.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/security/identity.py)<br>`apps/api/routes/verify.py` | `tests/integration/test_tiering.py`<br>`tests/unit/test_l3.py` | **Fully Met** |
| **D2** | **Quantum Digital Signatures (QDS) Key Distribution**<br>Information-theoretically secure multi-party signature distribution protocol using non-orthogonal states. | Teleportation-based six-state QDS protocol. Alice distributes non-orthogonal states $\{|0\rangle, |1\rangle, |+\rangle, |-\rangle, |i\rangle, |-i\rangle\}$. Bob and Charlie measure in independent secret bases $(X, Y, Z)$ and record outcomes. | [`src/qds/teleportation_qds.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/qds/teleportation_qds.py)<br>[`src/qds/key_material.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/qds/key_material.py)<br>`apps/api/routes/distribute.py`<br>`apps/api/routes/reveal.py` | `experiments/results/forgery_curve.csv`<br>`tests/integration/test_api.py` | **Fully Met** |
| **D3** | **Multi-Vector Threat Detection Engine**<br>Real-time detection of key forgery, classical impersonation, replay attacks, and channel manipulation. | 4-layer defense-in-depth architecture:<br>• L1: Teleportation simulation & length validation<br>• L2: Statistical binomial mismatch probe & tomography probe<br>• L3: ML-DSA authentication, timestamp guard, nonce guard<br>• L4: Correlation engine & tamper-evident ledger | [`src/detection/probes.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/detection/probes.py)<br>[`src/detection/correlation.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/detection/correlation.py)<br>[`src/detection/policy.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/detection/policy.py) | `experiments/results/multi_vector_matrix.csv`<br>`tests/integration/test_multivector.py` | **Fully Met** |
| **D4** | **Noise Calibration & Dynamic Threshold Derivation**<br>Empirically measured channel baseline noise and analytical detection threshold derivation. | Automated baseline measurement of channel mismatch $e_{\text{honest}}$ across noise levels; analytical derivation of thresholds $(\tau_{\text{low}}, \tau_{\text{high}})$ via binomial quantile derivation (`binom.ppf`) with full provenance recording. | [`src/calibration/measure_honest.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/calibration/measure_honest.py)<br>[`src/calibration/analytical.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/calibration/analytical.py)<br>`data/calibration/thresholds.json` | `experiments/results/noise_sweep.csv`<br>`tests/unit/test_calibration.py` | **Fully Met** |
| **D5** | **Transferability & Dispute Resolution Protocol**<br>Protection against verifier forgery and dispute arbitration (distinguishing signatures from MACs). | Dual-threshold evaluation rule ($\tau_{\text{low}}, \tau_{\text{high}}$). Bob cannot forge against Charlie because Bob does not know Charlie's measurement bases. Disagreement between primary and secondary verifiers triggers dedicated transferability findings. | [`src/detection/policy.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/detection/policy.py)<br>[`attacker/scenarios/forgery_by_verifier.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/attacker/scenarios/forgery_by_verifier.py) | `tests/integration/test_transferability.py`<br>`python -m attacker.runner --attack forgery_by_verifier` | **Fully Met** |
| **D6** | **Immutable Cryptographic Audit Trail (Ledger)**<br>Verifiable, append-only tamper-evident event storage with audit verification and checkpoint rollback detection. | SQLite-backed hash chain where each verification event includes an HMAC-SHA256 signature chained to the previous record's hash. Uses `BEGIN IMMEDIATE` for race-free concurrency. Checkpoint verification detects tail truncation and rollback attacks. | [`src/ledger/hash_chain.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/ledger/hash_chain.py)<br>[`src/ledger/verifier.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/src/ledger/verifier.py)<br>`apps/api/routes/ledger.py` | `experiments/results/concurrent_campaign.csv`<br>`tests/unit/test_ledger_integrity.py` | **Fully Met** |
| **D7** | **Adversarial Testbed & Operator Channel Control**<br>Restricted testbed allowing authorized operators to inject quantum noise and simulate cyber threats. | Dedicated operator endpoint `POST /v1/testbed/channel` protected by bearer operator token (`x-operator-token`). Injects coherent $R_x, R_z$ rotations, depolarizing noise, and intercept-resend attacks. Fully decoupled from participant verification payloads. | [`apps/api/routes/testbed.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/apps/api/routes/testbed.py)<br>[`attacker/harness.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/attacker/harness.py) | `experiments/results/adaptive_x.csv`<br>`tests/integration/test_api.py` | **Fully Met** |
| **D8** | **Side-Channel Mitigation & Response Tiering**<br>Constant-time response envelopes and role-based disclosure to prevent adversary reconnaissance. | Strict constant-time padding (40ms floor) on all verification return paths; authenticated role-based response tiering (registered auditors receive unredacted diagnostics; standard verifiers receive redacted security policy notices on REJECT). | [`apps/api/routes/verify.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/apps/api/routes/verify.py) | `experiments/results/latency_split.csv`<br>`tests/integration/test_tiering.py` | **Fully Met** |
| **D9** | **Empirical Evaluation & Performance Benchmarks**<br>Reproducible scientific evidence of threat detection performance, ROC curves, and throughput scaling. | Comprehensive automated experiment suite generating 9 CSV datasets in `experiments/results/` covering noise sweeps, rotation detection, blind evaluations, ROC curves, concurrency scaling, and latency splits. | `Makefile` (`make evaluate`)<br>`experiments/*.py`<br>`experiments/results/*.csv` | `experiments/results/blind_eval.csv`<br>`experiments/results/roc_curve.csv` | **Fully Met** |
| **D10** | **Strict Zero-AI/ML Regulatory Compliance**<br>Adherence to problem statement ban on artificial intelligence / machine learning models. | Protocol decisions are strictly derived from quantum mechanics principles (no-cloning, information-disturbance) and analytical binomial hypothesis testing. Automated compliance test scans all files and requirements. | [`tests/unit/test_compliance.py`](file:///c:/Users/Jeevan%20Reddy/OneDrive/Desktop/sentinel/helloworld/tests/unit/test_compliance.py) | `tests/unit/test_compliance.py` (passes 100% with 0 violations) | **Fully Met** |

---

## Verification & Proof Commands

Reviewers can verify all deliverables locally without requiring external services or Docker:

```bash
# 1. Run all 89 automated tests (integration, unit, property, compliance)
python -m pytest tests/ -v

# 2. Run the full experimental evaluation suite and verify evidence files
make evaluate
ls -la experiments/results/

# 3. Verify transferability (signature-not-a-MAC proof)
python -m attacker.runner --attack forgery_by_verifier

# 4. Verify zero AI/ML compliance and secret key safety
python -m pytest tests/unit/test_compliance.py -v
```
