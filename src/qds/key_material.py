"""
Q-SENTINEL Key Material Generation.

Generates message-independent, single-use quantum key elements using a CSPRNG.
Maps classical bits to the six-state quantum ensemble: {|0⟩, |1⟩, |+⟩, |−⟩, |i⟩, |−i⟩}.
"""
import secrets
from typing import Dict, List, Tuple
from dataclasses import dataclass

# The mapping from 3-bit values (only using 6 of 8 values) to the six-state ensemble.
# 000, 001 -> Z basis (0, 1) -> |0>, |1>
# 010, 011 -> X basis (0, 1) -> |+>, |->
# 100, 101 -> Y basis (0, 1) -> |i>, |-i>
# 110, 111 -> reroll (to ensure uniformity)

@dataclass
class QuantumKeyElement:
    """Represents a single quantum key element."""
    basis: str  # 'X', 'Y', or 'Z'
    bit: int    # 0 or 1
    
    def __post_init__(self):
        if self.basis not in ('X', 'Y', 'Z'):
            raise ValueError(f"Invalid basis: {self.basis}")
        if self.bit not in (0, 1):
            raise ValueError(f"Invalid bit: {self.bit}")


def generate_key_element() -> QuantumKeyElement:
    """
    Generate a single quantum key element uniformly at random from the six-state ensemble.
    Uses secrets module (CSPRNG) for cryptographic randomness.
    """
    while True:
        # Generate 1 random byte, take bottom 3 bits (values 0-7)
        val = secrets.randbits(3)
        if val < 6:
            # Map 0,1 -> Z; 2,3 -> X; 4,5 -> Y
            basis_idx = val // 2
            bit = val % 2
            basis = ['Z', 'X', 'Y'][basis_idx]
            return QuantumKeyElement(basis=basis, bit=bit)
        # Reroll if 6 or 7 to maintain uniform distribution across all 6 states


def generate_key_set(L: int) -> Tuple[List[QuantumKeyElement], List[QuantumKeyElement]]:
    """
    Generate a complete key set for a message of length 1 bit.
    A key set consists of two sequences of length L: one for bit '0' and one for bit '1'.
    
    Args:
        L: The security parameter (number of key elements per sequence).
        
    Returns:
        (k_0, k_1): A tuple containing the list of key elements for message bit 0, 
                    and the list of key elements for message bit 1.
    """
    k_0 = [generate_key_element() for _ in range(L)]
    k_1 = [generate_key_element() for _ in range(L)]
    return k_0, k_1

