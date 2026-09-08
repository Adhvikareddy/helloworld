"""
Pauli Correction for Teleportation-Based QDS.

After the Bell-basis measurement on qubits q0 and q1, the receiver (q2) must
apply Pauli corrections conditioned on the two classical bits:

  c1 = 1  →  apply X (bit-flip) to q2
  c0 = 1  →  apply Z (phase-flip) to q2

This restores the teleported state on q2 regardless of the Bell-measurement
outcome.  Without correction the teleported state is one of four equally
likely rotations of the original.

In the Qiskit circuit this is implemented using classical conditioning:
  qc.x(qr[2]).c_if(cr[1], 1)
  qc.z(qr[2]).c_if(cr[0], 1)
"""
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister


def apply_pauli_correction(
    qc: QuantumCircuit,
    qr: QuantumRegister,
    cr: ClassicalRegister,
    target_qubit: int = 2,
) -> None:
    """
    Apply classically-conditioned Pauli correction to the target qubit.

    Parameters
    ----------
    qc : QuantumCircuit
        The circuit being constructed.
    qr : QuantumRegister
        Quantum register (at least 3 qubits).
    cr : ClassicalRegister
        Classical register where cr[0] and cr[1] hold Bell-measurement results.
    target_qubit : int
        Index of the receiver qubit in qr (default 2).
    """
    qc.x(qr[target_qubit]).c_if(cr[1], 1)
    qc.z(qr[target_qubit]).c_if(cr[0], 1)
