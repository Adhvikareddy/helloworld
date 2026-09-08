"""
Q-SENTINEL Calibration — Grid Search with Real Qiskit Measurements.

This script:
  1. Runs the TeleportationQDS circuit at disturbance=0.0 multiple times
     to compute the legitimate baseline (mu) from actual Qiskit-Aer shots.
  2. Runs the circuit at multiple disturbance levels to collect adversarial
     deviation scores.
  3. Grid-searches for optimal (tau_low, tau_high) thresholds that separate
     legitimate from adversarial distributions.
  4. Freezes the calibrated baseline and thresholds to disk.

All values are derived from actual simulator execution — no hardcoded
baselines or guessed thresholds.
"""
from src.qds.teleportation_qds import TeleportationQDS
from src.detection.baseline import BaselineManager
from src.detection.statistics import DetectorStatistics
from src.detection.policy import DecisionPolicy
import numpy as np


def compute_baseline(qds: TeleportationQDS, runs: int = 30, shots: int = 1024) -> dict:
    """
    Execute legitimate QDS verification multiple times and compute
    mean (mu) and standard deviation (sigma) of the X/Y/Z probabilities.
    """
    # Collect probabilities across runs
    all_probs = {basis: {"0": [], "1": []} for basis in ["X", "Y", "Z"]}

    for i in range(runs):
        # Use different seeds per run for statistical diversity
        qds_run = TeleportationQDS(seed=100 + i)
        result = qds_run.execute_verification(shots=shots, disturbance_prob=0.0)
        for basis in ["X", "Y", "Z"]:
            for outcome in ["0", "1"]:
                all_probs[basis][outcome].append(
                    result["basis_probabilities"][basis][outcome]
                )

    mu = {}
    sigma = {}
    for basis in ["X", "Y", "Z"]:
        mu[basis] = {}
        sigma[basis] = {}
        for outcome in ["0", "1"]:
            vals = all_probs[basis][outcome]
            mu[basis][outcome] = float(np.mean(vals))
            sigma[basis][outcome] = float(np.std(vals))

    return mu, sigma


def collect_deviation_scores(
    qds: TeleportationQDS,
    mu: dict,
    disturbance_levels: list,
    runs_per_level: int = 20,
    shots: int = 1024,
) -> dict:
    """
    For each disturbance level, run the QDS circuit and compute D scores.
    Returns {level: [D_1, D_2, ...]}
    """
    scores = {}
    for dist in disturbance_levels:
        level_scores = []
        for i in range(runs_per_level):
            qds_run = TeleportationQDS(seed=500 + i)
            result = qds_run.execute_verification(shots=shots, disturbance_prob=dist)
            p_hat = result["basis_probabilities"]
            D = DetectorStatistics.compute_deviation(p_hat, mu)
            level_scores.append(D)
        scores[dist] = level_scores
    return scores


def grid_search_thresholds(
    legitimate_scores: list,
    adversarial_scores: dict,
) -> tuple:
    """
    Search for (tau_low, tau_high) that best separates legitimate from
    adversarial deviation scores.

    Strategy:
      tau_low  = max(legitimate D scores) + small margin
      tau_high = median of the lowest adversarial level's D scores

    This ensures:
      - All legitimate requests are ACCEPTed (D <= tau_low)
      - Clear adversarial signals are REJECTed (D > tau_high)
      - Borderline cases are QUARANTINEd (tau_low < D <= tau_high)
    """
    leg_max = max(legitimate_scores)
    margin = 0.01

    # Use the lowest adversarial disturbance level for QUARANTINE boundary
    lowest_adv_level = min(adversarial_scores.keys())
    lowest_adv_scores = adversarial_scores[lowest_adv_level]

    tau_low = round(leg_max + margin, 4)
    tau_high = round(float(np.median(lowest_adv_scores)), 4)

    # Ensure tau_high > tau_low
    if tau_high <= tau_low:
        tau_high = round(tau_low + margin, 4)

    return tau_low, tau_high


def run_calibration(
    shots: int = 1024,
    baseline_runs: int = 30,
    adversarial_runs: int = 20,
    baseline_path: str = "data/calibration/baseline.json",
    threshold_path: str = "data/calibration/thresholds.json",
):
    """Full calibration pipeline: baseline → grid search → freeze."""
    print("=" * 60)
    print("  Q-SENTINEL Calibration (Real Qiskit Measurements)")
    print("=" * 60)

    qds = TeleportationQDS(seed=42)

    # Step 1: Compute legitimate baseline from actual measurements
    print(f"\n[1/4] Computing legitimate baseline ({baseline_runs} runs x {shots} shots)...")
    mu, sigma = compute_baseline(qds, runs=baseline_runs, shots=shots)
    print(f"  Baseline mu:")
    for basis in ["X", "Y", "Z"]:
        print(f"    {basis}: P(0)={mu[basis]['0']:.4f}  P(1)={mu[basis]['1']:.4f}"
              f"  std(0)={sigma[basis]['0']:.4f}  std(1)={sigma[basis]['1']:.4f}")

    # Step 2: Collect legitimate deviation scores
    print(f"\n[2/4] Computing legitimate D scores ({baseline_runs} runs)...")
    leg_scores = []
    for i in range(baseline_runs):
        qds_run = TeleportationQDS(seed=200 + i)
        result = qds_run.execute_verification(shots=shots, disturbance_prob=0.0)
        p_hat = result["basis_probabilities"]
        D = DetectorStatistics.compute_deviation(p_hat, mu)
        leg_scores.append(D)
    print(f"  Legitimate D: min={min(leg_scores):.6f}  max={max(leg_scores):.6f}"
          f"  mean={np.mean(leg_scores):.6f}")

    # Step 3: Collect adversarial deviation scores
    disturbance_levels = [0.10, 0.25, 0.50]
    print(f"\n[3/4] Computing adversarial D scores ({adversarial_runs} runs x {len(disturbance_levels)} levels)...")
    adv_scores = collect_deviation_scores(qds, mu, disturbance_levels,
                                          runs_per_level=adversarial_runs, shots=shots)
    for level, scores in adv_scores.items():
        print(f"  Disturbance {level:.2f}: min={min(scores):.6f}  max={max(scores):.6f}"
              f"  mean={np.mean(scores):.6f}")

    # Step 4: Grid search and freeze
    print(f"\n[4/4] Grid searching thresholds...")
    tau_low, tau_high = grid_search_thresholds(leg_scores, adv_scores)
    print(f"  tau_low  = {tau_low}")
    print(f"  tau_high = {tau_high}")

    # Save
    baseline_mgr = BaselineManager(filepath=baseline_path)
    baseline_mgr.save_baseline(mu, sigma, "v1-qiskit-calibrated")

    decision_policy = DecisionPolicy(filepath=threshold_path)
    decision_policy.save_thresholds(tau_low, tau_high, "v1-qiskit-calibrated")

    print(f"\n{'=' * 60}")
    print(f"  Calibration COMPLETE")
    print(f"  Baseline: {baseline_path} (version: v1-qiskit-calibrated)")
    print(f"  Thresholds: {threshold_path} (tau_low={tau_low}, tau_high={tau_high})")
    print(f"{'=' * 60}")

    return {
        "mu": mu,
        "sigma": sigma,
        "tau_low": tau_low,
        "tau_high": tau_high,
        "legitimate_D_range": [min(leg_scores), max(leg_scores)],
        "adversarial_D_ranges": {
            level: [min(scores), max(scores)]
            for level, scores in adv_scores.items()
        },
    }


if __name__ == "__main__":
    run_calibration()
