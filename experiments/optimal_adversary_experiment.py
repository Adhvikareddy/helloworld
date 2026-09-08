"""
Q-SENTINEL Optimal Adversary Bound Experiment (Differentiator D2).

Verifies the optimal adversary discrimination probability for the six-state
ensemble and generates the forgery probability curve as a function of L.

Uses pure Python binomial computation (no scipy dependency).

Outputs: experiments/results/optimal_adversary.csv
"""
import csv
import os
import math
from src.detection.optimal_adversary import (
    analytical_optimal_prob,
    verify_sdp_bound,
)


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


def _log_binom_coeff(n: int, k: int) -> float:
    """Compute log(C(n, k)) using math.lgamma for stability."""
    if k < 0 or k > n:
        return float('-inf')
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def run_optimal_adversary_experiment():
    """
    Generates the full optimal adversary analysis:
    1. Verifies the SDP bound
    2. Computes P_forge as a function of L
    3. Outputs to CSV
    """
    print("=" * 60)
    print("  Q-SENTINEL Optimal Adversary Bound Experiment (D2)")
    print("=" * 60)
    
    # Step 1: Verify the SDP bound
    print("\n[1/3] Verifying SDP bound...")
    sdp_result = verify_sdp_bound()
    for k, v in sdp_result.items():
        print(f"  {k}: {v}")
    
    p_opt = analytical_optimal_prob()
    p_error = 1 - p_opt  # ≈ 0.2113 — the adversary's per-element error rate
    
    print(f"\n  p_opt = {p_opt:.6f}")
    print(f"  p_error (per element) = {p_error:.6f}")
    
    # Step 2: Compute P_forge for various L values and acceptance thresholds
    print("\n[2/3] Computing forgery probability curves...")
    
    # Realistic thresholds
    s_a = 0.05   # acceptance threshold
    e_honest = 0.01  # expected honest mismatch rate (from noise)
    
    L_values = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 
                450, 600, 900, 1200, 1500, 2000, 3000]
    
    results = []
    for L in L_values:
        n = L // 3  # Expected matched subset size
        if n == 0:
            continue
            
        # Number of mismatches the forger can "afford" and still be accepted
        max_mismatches = int(math.floor(s_a * n))
        
        # P_forge = P(Binomial(n, p_error) <= max_mismatches)
        p_forge = binomial_cdf(max_mismatches, n, p_error)
        
        # Also compute the honest acceptance probability
        p_honest_accept = binomial_cdf(max_mismatches, n, e_honest)
        
        security_bits = -math.log2(max(p_forge, 1e-300))
        
        results.append({
            "L": L,
            "n_matched": n,
            "s_a": s_a,
            "max_mismatches": max_mismatches,
            "p_forge": p_forge,
            "p_honest_accept": p_honest_accept,
            "security_bits": security_bits,
        })
        
        print(f"  L={L:5d}  n={n:4d}  P_forge={p_forge:.4e}  "
              f"Security={security_bits:6.1f} bits  "
              f"P_honest={p_honest_accept:.6f}")
    
    # Step 3: Save results
    print("\n[3/3] Saving results...")
    os.makedirs("experiments/results", exist_ok=True)
    output_path = "experiments/results/optimal_adversary.csv"
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    print(f"  Saved to {output_path}")
    
    # Summary
    # Find the L=300 result
    l300 = next((r for r in results if r["L"] == 300), None)
    l3000 = results[-1]
    
    print(f"\n{'=' * 60}")
    print(f"  SUMMARY")
    print(f"  p_opt (optimal adversary) = {p_opt:.6f}")
    print(f"  Acceptance threshold s_a  = {s_a}")
    print(f"  Honest error rate         = {e_honest}")
    if l300:
        print(f"  At L=300 (default):  P_forge = {l300['p_forge']:.4e} "
              f"({l300['security_bits']:.1f} security bits)")
    print(f"  At L=3000:           P_forge = {l3000['p_forge']:.4e} "
          f"({l3000['security_bits']:.1f} security bits)")
    print(f"{'=' * 60}")
    
    return results


if __name__ == "__main__":
    run_optimal_adversary_experiment()
