"""
Q-SENTINEL Reveal-and-Check Verification.

Handles the classical verification phase of the QDS protocol.
Compares Bob's stored measurement outcomes against the classical key elements
revealed by Alice, over the matched subset.
"""
from typing import List, Tuple
from src.qds.key_material import QuantumKeyElement

def compute_mismatch_rate(
    revealed_keys: List[QuantumKeyElement],
    bob_bases: List[str],
    bob_outcomes: List[int]
) -> Tuple[float, int, int]:
    """
    Compute the mismatch rate for the revealed keys against Bob's measurements.
    
    Args:
        revealed_keys: The list of classical key descriptions revealed by Alice.
        bob_bases: The sequence of measurement bases Bob chose.
        bob_outcomes: The sequence of measurement outcomes Bob obtained.
        
    Returns:
        (mismatch_rate, mismatches, matched_subset_size)
    """
    if len(revealed_keys) != len(bob_bases) or len(bob_bases) != len(bob_outcomes):
        raise ValueError("Lengths of keys, bases, and outcomes must match.")
        
    mismatches = 0
    matched_subset_size = 0
    
    for alice_k, bob_basis, bob_outcome in zip(revealed_keys, bob_bases, bob_outcomes):
        # The matched subset consists of positions where Bob randomly chose 
        # the same basis that Alice used to prepare her state.
        if alice_k.basis == bob_basis:
            matched_subset_size += 1
            if alice_k.bit != bob_outcome:
                mismatches += 1
                
    if matched_subset_size == 0:
        return 0.0, 0, 0
        
    return mismatches / matched_subset_size, mismatches, matched_subset_size

