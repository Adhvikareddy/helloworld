# Q-SENTINEL Threat Model

This document outlines the specific attack vectors covered by the Q-SENTINEL adversarial test harness.

## 1. Forgery A (Invalid Signature Path)
**Target:** L1 (Verification Core)
The attacker possesses a tampered or completely invalid digital signature but attempts to bypass cryptographic validation. The system must hard-fail before executing quantum circuits.

## 2. Forgery B (Valid-Path Quantum Forgery)
**Target:** L1 / L2 (Statistical Detector)
The attacker possesses a valid classical signature envelope but does not know the quantum key elements. The attacker guesses the states, resulting in a significantly elevated mismatch rate. The statistical detector must reliably reject this above the $p_{opt}$ baseline.

## 3. Impersonation
**Target:** L3 (Security Guard) / Envelope Verification
The attacker attempts to claim the identity of a different registered participant. The ML-DSA-65 signature on the request envelope will fail to match the claimed identity's public key.

## 4. Replay Attacks
**Target:** L3 (Nonce Guard)
The attacker captures a fully valid, previously accepted verification request and resubmits it identically. The system must track nonces and session IDs to reject duplicates immediately.

## 5. Unauthorized Verification
**Target:** L3 (Authorization Guard)
An unregistered or revoked entity attempts to invoke the verification endpoint. The system must deny access based on the PQC identity envelope before executing any business logic.

## 6. Channel Manipulation
**Target:** L2 (Statistical Detector)
The attacker introduces controlled rotations ($R_x$, $R_y$, $R_z$) on the quantum channel, degrading state fidelity. The system must observe the statistical deviation and either quarantine or reject the request depending on the severity of the disturbance compared to the calibration baseline.

## 7. Ledger Tampering
**Target:** L4 (Evidence Ledger)
The attacker gains direct write access to the SQLite database file and modifies a historic verification event's verdict. The HMAC-SHA256 chain verification must detect the integrity failure and flag the specific tampered record.
