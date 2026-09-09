# Q-SENTINEL Limitations & Constraints

## 1. Scope of Signed Message
**Single-Bit Signature Protocol:** The current construction strictly signs **one bit ($m \in \{0, 1\}$) per session**. It does **not** sign arbitrary-length messages or documents directly. For each signature, Alice distributes two independent key sequences ($K_0$ and $K_1$), each of length $L$, and reveals only the key sequence corresponding to the message bit $m$. To sign an $n$-bit message or document digest, $n$ independent parallel distribution sessions must be executed. Do not assume or imply arbitrary-length message signing in this version.

## 2. Dataset Requirements and Google Drive PS Reference
The Smart India Hackathon problem statement carries an external reference link:
`https://drive.google.com/drive/folders/1rgGdaPn9rdGZfkaqc3MKVfdCK8r5X_gk`
labelled *"Additional Information Regarding PS"*.

**Access Status and Operational Risk:**
Direct programmatic retrieval of this URL yields a dynamic Single-Page Application (SPA) Google Drive shell titled "Egreen Quanta" requiring interactive Google authentication. No static, public tabular training or evaluation dataset could be retrieved automatically. 

This is documented explicitly as an **open risk**: while Q-SENTINEL's protocol operates autonomously as an information-theoretic quantum digital signature scheme generating its own single-use quantum key states and measuring channel baselines dynamically (producing `experiments/results/noise_sweep.csv`), access to any proprietary vendor hardware datasets or specific optical channel trace files from that folder remains subject to manual retrieval by the organizing committee.

## 3. Operating Environment
**Python Version Compatibility:** The development environment executes on Python 3.14.0, while the production container specification targets Python 3.11. All quantum circuit generation, simulation, and cryptographic primitives (Qiskit 1.1.1, Qiskit-Aer 0.14.2, pure Python reference ML-DSA-65) have been verified to execute identically across versions. The production deployment in `docker-compose.yml` pins `python:3.11-slim`.

**Operating System Isolation:** Native execution on Windows enforces isolation boundaries via Python process boundaries, environment variables, and SQLite immediate write locks. Full POSIX-compliant multi-user filesystem isolation (`chmod 600`) is provided in the Docker container architecture.

## 4. Protocol & Hardware Limitations
- **Quantum Simulation vs. Physical Hardware:** Verification is performed via IBM Qiskit-Aer statevector and density-matrix quantum circuit simulation. Physical optical fibers, photon detectors, and quantum hardware attenuation are modeled via Kraus noise operators, depolarizing channels, and coherent rotation operators ($R_x, R_z$), but do not execute on physical cryo-QPUs due to multi-minute cloud queuing constraints.
- **Evidence Ledger:** The append-only hash chain uses HMAC-SHA256 with sequence numbering to provide tamper-evident cryptographic proofs. It is a centralized high-throughput microservice ledger, not a decentralized Byzantine-fault-tolerant blockchain consensus network.
- **Zero AI/ML Invariant:** The architecture strictly avoids any machine learning models, neural networks, or trained classifiers. The detection layer is mathematical and physics-based, executing binomial hypothesis testing, Clopper–Pearson intervals, and quantum state tomography.
