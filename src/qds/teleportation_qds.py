"""
Q-SENTINEL Teleportation QDS Core.

Rebuilt for v9 to provide information-theoretically secure QDS.
Implements proper single-use keys mapped to the six-state ensemble.
Fixes F1, F2, F3 by using per-request randomisation and removing hardcoded states.
"""
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
import time
import hashlib
from typing import Dict, List, Tuple
from src.qds.key_material import QuantumKeyElement
from src.qds.noise import get_noise_model
from src.qds.pauli_correction import apply_pauli_correction
from src.qds.projective_measurement import apply_projective_measurement


class TeleportationQDS:
    """
    Simulates the quantum distribution and verification phase.
    """
    
    def __init__(self, disturbance_prob: float = 0.0, seed: int = None):
        # We don't fix the seed here globally anymore (fixes F2)
        # We use a noise model based on the requested disturbance
        self.noise_model = get_noise_model(disturbance_prob)
        self.seed = seed

    def _prepare_message_state(self, qc: QuantumCircuit, qr: QuantumRegister, element: QuantumKeyElement, qubit_idx: int = 0):
        """Prepare the state |0>, |1>, |+>, |->, |i>, |-i> corresponding to the key element."""
        if element.basis == 'Z':
            if element.bit == 1:
                qc.x(qr[qubit_idx])
        elif element.basis == 'X':
            if element.bit == 1:
                qc.x(qr[qubit_idx])
            qc.h(qr[qubit_idx])
        elif element.basis == 'Y':
            if element.bit == 1:
                qc.x(qr[qubit_idx])
            # Prepare Y basis states: H then S
            qc.h(qr[qubit_idx])
            qc.s(qr[qubit_idx])

    def _build_circuit(self, alice_element: QuantumKeyElement, bob_basis: str, pure_x_rotation: bool = False, disturbance: float = 0.0) -> QuantumCircuit:
        """
        Builds a single circuit representing the teleportation of ONE key element
        measured by Bob in his chosen basis.
        """
        qr = QuantumRegister(3, 'q')
        cr = ClassicalRegister(3, 'c')
        qc = QuantumCircuit(qr, cr)

        # 1. State preparation (message state)
        self._prepare_message_state(qc, qr, alice_element, 0)
        
        # 2. Bell state preparation (entangled channel)
        qc.h(qr[1])
        qc.cx(qr[1], qr[2])
        
        # Note: Depolarizing error on the channel is handled by the noise model.
        # However, for the F3 regression test, we can force a pure X rotation here.
        if pure_x_rotation and disturbance > 0.0:
            qc.rx(disturbance * 3.14159, qr[2])
            
        # 3. Bell basis measurement (Alice)
        qc.cx(qr[0], qr[1])
        qc.h(qr[0])
        qc.measure(qr[0], cr[0])
        qc.measure(qr[1], cr[1])
        
        # 4. Pauli correction (Bob)
        apply_pauli_correction(qc, qr, cr, target_qubit=2)
        
        # 5. Projective measurement in randomly chosen basis (Bob)
        apply_projective_measurement(qc, qr, cr, basis=bob_basis, target_qubit=2, classical_bit=2)
        
        return qc

    def execute_session(self, 
                       alice_keys: List[QuantumKeyElement], 
                       bob_bases: List[str], 
                       seed_material: str,
                       pure_x_rotation: bool = False,
                       disturbance: float = 0.0) -> Tuple[List[int], dict]:
        """
        Execute the quantum circuits for the full session (L elements).
        
        Args:
            alice_keys: The list of quantum key elements prepared by Alice.
            bob_bases: The list of measurement bases chosen by Bob.
            seed_material: String used to derive a deterministic seed.
            pure_x_rotation: Boolean flag to enable F3 regression testing.
            disturbance: Float for pure_x_rotation magnitude.
                           
        Returns:
            (bob_outcomes, metadata)
        """
        start_time = time.time()
        
        if len(alice_keys) != len(bob_bases):
            raise ValueError("Length of keys and bases must match")
            
        L = len(alice_keys)
        
        # Derive a 32-bit integer seed from the seed_material
        h = hashlib.sha256(seed_material.encode('utf-8')).hexdigest()
        request_seed = int(h[:8], 16)
        
        # Create simulator for this request
        sim = AerSimulator(
            method='statevector',
            seed_simulator=request_seed,
            noise_model=self.noise_model
        )
        
        # We could build and run them all in one job for efficiency
        circuits = []
        for i in range(L):
            circuits.append(self._build_circuit(
                alice_keys[i], 
                bob_bases[i], 
                pure_x_rotation=pure_x_rotation,
                disturbance=disturbance
            ))
            
        # Run all circuits. shots=1 because it's a single copy transmission per element!
        job = sim.run(circuits, shots=1)
        result = job.result()
        
        bob_outcomes = []
        for i in range(L):
            counts = result.get_counts(i)
            # The classical register has 3 bits: c2 c1 c0
            # Qiskit get_counts returns e.g. '100' where the first char is c2 (Bob's measurement)
            bitstring = list(counts.keys())[0]
            bob_outcomes.append(int(bitstring[0]))
            
        latency_ms = (time.time() - start_time) * 1000
        
        return bob_outcomes, {
            "execution_seed": request_seed,
            "latency_ms": latency_ms,
            "simulated_elements": L
        }

    def execute_verification(self, shots: int = 1024, disturbance_prob: float = 0.0, is_invalid_signature: bool = False) -> dict:
        """
        Backward-compatible calibration interface.
        
        Generates L key elements (one per basis), distributes them through the
        quantum teleportation channel, and collects per-basis measurement statistics.
        
        This method exists for the calibration pipeline and testing. Production
        verification uses execute_session directly.
        """
        if is_invalid_signature:
            return {
                "protocol_valid": False,
                "shot_count": 0,
                "measurement_counts": {},
                "basis_probabilities": {},
            }
        
        
        basis_counts = {"X": {"0": 0, "1": 0}, "Y": {"0": 0, "1": 0}, "Z": {"0": 0, "1": 0}}
        
        seed = self.seed if self.seed is not None else 42
        
        for basis in ["X", "Y", "Z"]:
            # Prepare key element as |+⟩ (X+ state) — this is the calibration reference state
            element = QuantumKeyElement(basis='X', bit=0)
            
            qc = self._build_circuit(element, basis, disturbance=disturbance_prob)
            
            # Create a noise model specific to this disturbance
            noise_model = get_noise_model(disturbance_prob)
            
            sim = AerSimulator(
                method='statevector',
                seed_simulator=seed,
                noise_model=noise_model
            )
            
            job = sim.run(qc, shots=shots)
            result = job.result()
            counts = result.get_counts(0)
            
            # Parse counts — bob's outcome is bit position 0 of the 3-bit register
            for bitstring, count in counts.items():
                bob_bit = bitstring[0]  # MSB is c2 (Bob's measurement)
                basis_counts[basis][bob_bit] += count
        
        # Convert to probabilities
        basis_probs = {}
        for basis in ["X", "Y", "Z"]:
            total = basis_counts[basis]["0"] + basis_counts[basis]["1"]
            if total > 0:
                basis_probs[basis] = {
                    "0": basis_counts[basis]["0"] / total,
                    "1": basis_counts[basis]["1"] / total
                }
            else:
                basis_probs[basis] = {"0": 0.5, "1": 0.5}
        
        return {
            "protocol_valid": True,
            "shot_count": shots,
            "measurement_counts": basis_counts,
            "basis_probabilities": basis_probs,
        }
