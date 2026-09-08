"""
Q-SENTINEL Statistical Utilities.

Includes:
  - DetectorStatistics: Deviation and chi-square computation for the statistical detector.
  - holm_bonferroni_correction: Family-wise error rate control across multiple tests.
"""
from typing import List, Dict, Optional


class DetectorStatistics:
    """
    Computes deviation D and chi-square statistics for comparing
    observed measurement probabilities against the calibrated baseline.
    """

    @staticmethod
    def compute_deviation(
        p_hat: Dict[str, Dict[str, float]],
        mu: Dict[str, Dict[str, float]],
        weights: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> float:
        """
        Compute the weighted sum-of-squared-errors deviation D between
        observed probabilities p_hat and baseline mu.

        D = Σ_{basis} Σ_{outcome} w_{basis,outcome} * (p_hat - mu)^2

        Default weights are 1.0 for all entries.
        """
        D = 0.0
        for basis in p_hat:
            if basis not in mu:
                continue
            for outcome in p_hat[basis]:
                if outcome not in mu[basis]:
                    continue
                diff = p_hat[basis][outcome] - mu[basis][outcome]
                w = 1.0
                if weights and basis in weights and outcome in weights[basis]:
                    w = weights[basis][outcome]
                D += w * diff * diff
        return D

    @staticmethod
    def compute_chi_square(
        p_hat: Dict[str, Dict[str, float]],
        mu: Dict[str, Dict[str, float]],
        N: int,
        epsilon: float = 1e-10,
    ) -> float:
        """
        Compute the chi-square statistic:
          χ² = N · Σ (p_hat - mu)^2 / (mu + epsilon)

        N = number of shots.  epsilon prevents division by zero.
        """
        chi2 = 0.0
        for basis in p_hat:
            if basis not in mu:
                continue
            for outcome in p_hat[basis]:
                if outcome not in mu[basis]:
                    continue
                diff = p_hat[basis][outcome] - mu[basis][outcome]
                chi2 += N * (diff ** 2) / (mu[basis][outcome] + epsilon)
        return chi2


def holm_bonferroni_correction(p_values: List[float], alpha: float) -> List[bool]:
    """
    Apply the Holm-Bonferroni correction to control the Family-Wise Error Rate (FWER).
    
    Args:
        p_values: A list of p-values from multiple independent hypothesis tests.
        alpha: The target family-wise error rate.
        
    Returns:
        A list of booleans indicating whether each corresponding null hypothesis is rejected.
        True = Reject Null (e.g., Reject the hypothesis that the signature is honest -> Forgery).
        False = Fail to Reject Null.
    """
    m = len(p_values)
    if m == 0:
        return []
        
    # Sort p-values along with their original indices
    sorted_p = sorted(enumerate(p_values), key=lambda x: x[1])
    
    results = [False] * m
    
    # Step down procedure
    for k, (original_idx, p) in enumerate(sorted_p):
        # The adjusted threshold for the k-th smallest p-value (0-indexed) is alpha / (m - k)
        adj_alpha = alpha / (m - k)
        
        if p <= adj_alpha:
            results[original_idx] = True
        else:
            # Once we fail to reject, we stop and fail to reject all remaining
            break
            
    return results

