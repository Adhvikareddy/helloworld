from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
import time
import json

class TeleportationQDS:
    """
    Reference teleportation-based QDS using Qiskit-Aer.
    """
    def __init__(self, seed: int = 42):
        self.simulator = AerSimulator(method='statevector', seed_simulator=seed)
        self.seed = seed

    def _build_circuit(self, basis: str, disturbance_prob: float = 0.0) -> QuantumCircuit:
        qr = QuantumRegister(3, 'q')
        cr = ClassicalRegister(3, 'c')
        qc = QuantumCircuit(qr, cr)

        # 1. State preparation (message state) - say |+> state
        qc.h(qr[0])
        
        # 2. Bell state preparation
        qc.h(qr[1])
        qc.cx(qr[1], qr[2])
        
        # 3. Channel Disturbance (Simulated by rotations if requested)
        if disturbance_prob > 0:
            qc.rx(disturbance_prob * 3.14159, qr[2])
            qc.rz(disturbance_prob * 3.14159, qr[2])
            
        # 4. Bell basis measurement
        qc.cx(qr[0], qr[1])
        qc.h(qr[0])
        qc.measure(qr[0], cr[0])
        qc.measure(qr[1], cr[1])
        
        # 5. Pauli correction
        qc.x(qr[2]).c_if(cr[1], 1)
        qc.z(qr[2]).c_if(cr[0], 1)
        
        # 6. Projective measurement in X, Y, Z
        if basis == 'X':
            qc.h(qr[2])
        elif basis == 'Y':
            qc.sdg(qr[2])
            qc.h(qr[2])
        # For Z, do nothing
        
        qc.measure(qr[2], cr[2])
        return qc

    def execute_verification(self, shots: int, disturbance_prob: float = 0.0, is_invalid_signature: bool = False) -> dict:
        start_time = time.time()
        
        if is_invalid_signature:
            # L1 QDS Validity failure
            return {
                "protocol_valid": False,
                "measurement_counts": {},
                "basis_probabilities": {},
                "shot_count": shots,
                "execution_metadata": {"latency_ms": (time.time() - start_time) * 1000}
            }

        basis_probabilities = {}
        measurement_counts = {}
        
        for basis in ['X', 'Y', 'Z']:
            qc = self._build_circuit(basis, disturbance_prob)
            job = self.simulator.run(qc, shots=shots)
            counts = job.result().get_counts(qc)
            measurement_counts[basis] = counts
            
            # Extract probability of the teleported qubit measurement (c_2)
            # counts keys are like 'c2 c1 c0' e.g. '0 1 0' if spaces or '010'
            # Qiskit returns 'c2 c1 c0' without spaces by default: 'xyz' where x is c2
            total = sum(counts.values())
            c2_0 = sum(v for k, v in counts.items() if k.startswith('0'))
            c2_1 = sum(v for k, v in counts.items() if k.startswith('1'))
            
            basis_probabilities[basis] = {
                "0": c2_0 / total,
                "1": c2_1 / total
            }
            
        latency = (time.time() - start_time) * 1000
        
        return {
            "protocol_valid": True,
            "measurement_counts": measurement_counts,
            "basis_probabilities": basis_probabilities,
            "shot_count": shots,
            "execution_metadata": {
                "seed": self.seed,
                "latency_ms": latency
            }
        }
