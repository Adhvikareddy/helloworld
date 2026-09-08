"""
Projective Measurement for Teleportation-Based QDS.

After Pauli correction the receiver qubit (q2) holds the teleported state.
To characterise the state we measure in three mutually unbiased bases:

  X-basis:  apply H then measure          (eigenstates |+⟩, |-⟩)
  Y-basis:  apply S† then H then measure  (eigenstates |i⟩, |-i⟩)
  Z-basis:  measure directly              (eigenstates |0⟩, |1⟩)

The three measurement distributions together provide a tomographic
fingerprint that the L2 detector compares against the calibrated baseline.
"""
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister


def apply_projective_measurement(
    qc: QuantumCircuit,
    qr: QuantumRegister,
    cr: ClassicalRegister,
    basis: str,
    target_qubit: int = 2,
    classical_bit: int = 2,
) -> None:
    """
    Apply the basis rotation and measure the target qubit.

    Parameters
    ----------
    qc : QuantumCircuit
        The circuit being constructed.
    qr : QuantumRegister
        Quantum register.
    cr : ClassicalRegister
        Classical register.
    basis : str
        One of 'X', 'Y', 'Z'.
    target_qubit : int
        Index of the qubit to measure in qr (default 2).
    classical_bit : int
        Index of the classical bit to store the result (default 2).

    Raises
    ------
    ValueError
        If basis is not one of 'X', 'Y', 'Z'.
    """
    basis = basis.upper()
    if basis == "X":
        qc.h(qr[target_qubit])
    elif basis == "Y":
        qc.sdg(qr[target_qubit])
        qc.h(qr[target_qubit])
    elif basis == "Z":
        pass  # computational basis — no rotation needed
    else:
        raise ValueError(f"Unknown measurement basis: {basis!r}. Use 'X', 'Y', or 'Z'.")

    qc.measure(qr[target_qubit], cr[classical_bit])
