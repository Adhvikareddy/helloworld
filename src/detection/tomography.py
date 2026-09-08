"""
Q-SENTINEL Channel Tomography (Differentiator D1).

Reconstructs the quantum channel error profile from measurement statistics
to attribute attack type (depolarizing vs coherent rotation vs measurement tampering).
"""
import numpy as np
from typing import Dict, List, Tuple
from src.qds.key_material import QuantumKeyElement


def compute_basis_mismatch_rates(
    alice_keys: List[QuantumKeyElement],
    bob_bases: List[str],
    bob_outcomes: List[int]
) -> Dict[str, Dict[str, float]]:
    """
    Compute per-basis mismatch rates for channel tomography.
    
    Returns a dict like:
    {
        "X": {"mismatches": 5, "total": 30, "rate": 0.167},
        "Y": {"mismatches": 3, "total": 28, "rate": 0.107},
        "Z": {"mismatches": 4, "total": 32, "rate": 0.125},
    }
    """
    basis_stats: Dict[str, Dict[str, int]] = {
        "X": {"mismatches": 0, "total": 0},
        "Y": {"mismatches": 0, "total": 0},
        "Z": {"mismatches": 0, "total": 0},
    }
    
    for i in range(len(alice_keys)):
        if alice_keys[i].basis == bob_bases[i]:
            basis = alice_keys[i].basis
            basis_stats[basis]["total"] += 1
            if bob_outcomes[i] != alice_keys[i].bit:
                basis_stats[basis]["mismatches"] += 1
    
    result = {}
    for basis, stats in basis_stats.items():
        total = stats["total"]
        mismatches = stats["mismatches"]
        result[basis] = {
            "mismatches": mismatches,
            "total": total,
            "rate": mismatches / total if total > 0 else 0.0
        }
    
    return result


def classify_attack(basis_rates: Dict[str, Dict[str, float]]) -> Dict[str, any]:
    """
    Classify the attack type based on per-basis mismatch rate profile.
    
    Attack signatures:
    - Depolarizing noise: uniform error across all bases (X ≈ Y ≈ Z)
    - Pure X rotation:    high error on Y,Z bases, low on X
    - Pure Z rotation:    high error on X,Y bases, low on Z
    - Measurement attack: elevated error on specific basis pairs
    - No attack:          all rates near zero
    """
    rates = {b: basis_rates[b]["rate"] for b in ["X", "Y", "Z"]}
    totals = {b: basis_rates[b]["total"] for b in ["X", "Y", "Z"]}
    
    # Need minimum samples per basis for reliable classification
    min_samples = 5
    if any(totals[b] < min_samples for b in ["X", "Y", "Z"]):
        return {
            "classification": "INSUFFICIENT_DATA",
            "confidence": 0.0,
            "basis_rates": rates,
            "description": "Not enough matched samples per basis for reliable classification."
        }
    
    avg_rate = sum(rates.values()) / 3
    
    if avg_rate < 0.02:
        return {
            "classification": "CLEAN",
            "confidence": 0.95,
            "basis_rates": rates,
            "description": "No significant channel disturbance detected."
        }
    
    # Check for uniformity (depolarizing)
    max_rate = max(rates.values())
    min_rate = min(rates.values())
    spread = max_rate - min_rate
    
    if spread < 0.05 and avg_rate > 0.02:
        return {
            "classification": "DEPOLARIZING",
            "confidence": min(0.95, 1.0 - spread / avg_rate),
            "basis_rates": rates,
            "description": f"Uniform noise across all bases (spread={spread:.4f}). "
                          f"Consistent with depolarizing channel or environmental noise."
        }
    
    # Check for axis-specific rotation
    # Pure X rotation affects Y and Z but not X
    if rates["X"] < avg_rate * 0.5 and rates["Y"] > avg_rate and rates["Z"] > avg_rate:
        return {
            "classification": "X_ROTATION",
            "confidence": 0.8,
            "basis_rates": rates,
            "description": "Elevated errors on Y,Z bases with low X error. "
                          "Consistent with a pure X-axis rotation attack."
        }
    
    # Pure Z rotation affects X and Y but not Z
    if rates["Z"] < avg_rate * 0.5 and rates["X"] > avg_rate and rates["Y"] > avg_rate:
        return {
            "classification": "Z_ROTATION",
            "confidence": 0.8,
            "basis_rates": rates,
            "description": "Elevated errors on X,Y bases with low Z error. "
                          "Consistent with a pure Z-axis rotation attack."
        }
    
    # Pure Y rotation affects X and Z but not Y
    if rates["Y"] < avg_rate * 0.5 and rates["X"] > avg_rate and rates["Z"] > avg_rate:
        return {
            "classification": "Y_ROTATION",
            "confidence": 0.8,
            "basis_rates": rates,
            "description": "Elevated errors on X,Z bases with low Y error. "
                          "Consistent with a pure Y-axis rotation attack."
        }
    
    # General coherent attack (non-uniform but doesn't match a single axis)
    return {
        "classification": "COHERENT_UNKNOWN",
        "confidence": 0.6,
        "basis_rates": rates,
        "description": f"Non-uniform error profile (spread={spread:.4f}). "
                      f"Possible coherent attack with mixed rotation axes."
    }
