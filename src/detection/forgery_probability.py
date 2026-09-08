"""
Q-SENTINEL Forgery Probability Analysis.

Implements the bounds for the six-state QDS protocol against an
individual-measurement adversary.
"""
import math


def _log_binom_coeff(n: int, k: int) -> float:
    """Compute log(C(n, k)) using math.lgamma for stability."""
    if k < 0 or k > n:
        return float('-inf')
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def binomial_cdf(k: int, n: int, p: float) -> float:
    """
    Compute P(X <= k) where X ~ Binomial(n, p).
    Pure Python implementation using log-space for numerical stability.
    """
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    
    # Sum P(X = i) for i = 0..k using log-space
    total = 0.0
    for i in range(k + 1):
        # log(C(n, i)) + i*log(p) + (n-i)*log(1-p)
        log_prob = _log_binom_coeff(n, i) + i * math.log(max(p, 1e-300)) + (n - i) * math.log(max(1 - p, 1e-300))
        total += math.exp(log_prob)
    
    return min(total, 1.0)


def optimal_adversary_success_prob() -> float:
    """
    Returns the optimal minimum-error discrimination probability
    for the six-state symmetric ensemble against an individual-measurement adversary.
    
    p_opt = (1 + 1/sqrt(3)) / 2  ≈ 0.7887
    """
    return (1 + 1 / math.sqrt(3)) / 2


def compute_forgery_probability(L: int, s_a: float) -> float:
    """
    Compute the probability that an adversary successfully forges a signature.
    
    The adversary must guess the states well enough that the mismatch rate
    on the matched subset is strictly less than the acceptance threshold s_a.
    
    Args:
        L: The security parameter (length of the key sequence).
        s_a: The acceptance mismatch threshold (e.g., 0.05).
        
    Returns:
        The upper bound on the forgery probability.
    """
    # The expected size of the matched subset when Bob chooses from 3 bases uniformly
    n_expected = L / 3.0
    
    # We use the floor of the expected size for a conservative bound,
    # or one could compute the exact sum over the binomial distribution of subset sizes.
    # For simplicity and standard bounding, we use the expected subset size.
    n = math.floor(n_expected)
    
    if n == 0:
        return 1.0
        
    p_opt = optimal_adversary_success_prob()
    
    # The adversary needs number of mismatches <= floor(s_a * n)
    # The number of mismatches follows a Binomial distribution with p_mismatch = 1 - p_opt
    max_mismatches = math.floor(s_a * n)
    
    prob = binomial_cdf(max_mismatches, n, 1 - p_opt)
    return float(prob)


def compute_required_L(target_prob: float, s_a: float) -> int:
    """
    Compute the required security parameter L to achieve a target forgery probability.
    
    Args:
        target_prob: The maximum acceptable forgery probability (e.g., 1e-6).
        s_a: The acceptance mismatch threshold.
        
    Returns:
        The required sequence length L.
    """
    L = 300  # Start with a reasonable guess
    while True:
        p = compute_forgery_probability(L, s_a)
        if p <= target_prob:
            return L
        L += 3  # Increment by 3 to add 1 to expected subset size
