# Q-SENTINEL Limitations & Constraints

## 1. Operating Environment
**Python Version Mismatch:** The development machine runs Python 3.14.0, while the specification requires Python 3.11. All quantum and classical cryptographic libraries (Qiskit 1.1.1, qiskit-aer 0.14.2, pqcrypto 1.0.0) have been verified to execute identically on 3.14.0. The Track B Docker images are pinned to `python:3.11-slim`.

**Windows vs Linux Isolation:** The Track A native deployment runs on Windows. OS-level filesystem isolation (using `chmod 600` and separate Unix user accounts) is a Linux mechanism. On Windows, isolation is enforced via Python process boundaries and environment variables. Full filesystem isolation is demonstrated in Track B Docker containers.

## 2. Protocol Limitations
- **Simulator Independence:** Qiskit-Aer executes the quantum circuit computationally. It does not reproduce physical hardware noise or actual photon transmission loss.
- **Ledger Immutability:** The HMAC-SHA256 hash chain provides tamper evidence. It is a local data structure, not decentralized blockchain consensus.
- **Zero AI/ML:** The implementation contains no machine learning, no neural networks, and no classifiers. The detection layer is strictly statistical (empirical distributions, Clopper–Pearson intervals, $\chi^2$ divergence).
- **Post-Quantum Cryptography:** The transport layer uses Module-Lattice DSA (ML-DSA-65) for authentication. This is an algorithmic standard (FIPS 204), not an ML model.

## 3. Dataset Requirements
The SIH Problem Statement specifies a "Dataset" tag, but no external dataset is consumed. The Q-SENTINEL protocol inherently generates its own data via Qiskit-Aer simulation of the six-state quantum digital signature protocol. Calibration relies entirely on self-generated measurements.
