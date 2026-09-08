"""
Q-SENTINEL Analytical Threshold Derivation.

Derives the acceptance threshold (s_a) analytically based on a target
false positive rate (alpha) rather than fitting to empirical adversarial data.
"""
from scipy.stats import binom
import math

def derive_thresholds(n: int, p_err_honest: float, alpha: float = 1e-4) -> float:
    """
    Derive the acceptance threshold tau_low based on honest error rate and target FPR.
    
    Args:
        n: The size of the matched subset (expected L/3).
        p_err_honest: The base error rate of the honest quantum channel (e.g., from calibration).
        alpha: Target false positive rate (probability of rejecting an honest signature).
        
    Returns:
        tau_low: The threshold below which a signature is accepted.
    """
    if n == 0:
        return 1.0
        
    # We want to find the maximum number of mismatches k such that
    # P(Binomial(n, p_err_honest) > k) <= alpha
    # Equivalently, k is the (1 - alpha) quantile of Binomial(n, p_err_honest)
    
    # ppf is the inverse of cdf: returns the smallest value k such that cdf(k) >= 1 - alpha
    # Since we want the probability of exceeding k to be <= alpha, we want cdf(k) >= 1 - alpha.
    k_max = binom.ppf(1 - alpha, n, p_err_honest)
    
    # tau_low is the rate
    tau_low = k_max / n
    return float(tau_low)

