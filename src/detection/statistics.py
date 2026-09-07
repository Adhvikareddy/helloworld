class DetectorStatistics:
    """
    Computes statistical deviations for L2 Threat Detector.
    """
    @staticmethod
    def compute_deviation(p_hat: dict, mu: dict, weights: dict = None) -> float:
        D = 0.0
        for basis, outcomes in p_hat.items():
            for outcome, prob in outcomes.items():
                expected = mu.get(basis, {}).get(outcome, 0.0)
                w = weights.get(basis, {}).get(outcome, 1.0) if weights else 1.0
                D += w * (prob - expected)**2
        return D

    @staticmethod
    def compute_chi_square(p_hat: dict, mu: dict, N: int, epsilon: float = 1e-4) -> float:
        chi2 = 0.0
        for basis, outcomes in p_hat.items():
            for outcome, prob in outcomes.items():
                expected = max(mu.get(basis, {}).get(outcome, 0.0), epsilon)
                chi2 += N * (prob - expected)**2 / expected
        return chi2
