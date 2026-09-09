"""
Measurement of honest baseline error rate for Q-SENTINEL.

Runs legitimate distribute+verify cycles to measure the empirical error rate
and matched subset size under physical channel disturbance.
"""
import random
import secrets
import numpy as np
from typing import Dict, Any

from src.qds.teleportation_qds import TeleportationQDS
from src.qds.key_material import generate_key_set
from src.qds.verification import compute_mismatch_rate


def measure_honest_baseline(disturbance: float, trials: int = 30, L: int = 90) -> dict:
    """
    Run `trials` LEGITIMATE distribute+verify cycles at the given channel
    disturbance, using the TRUE revealed keys every time.

    Returns:
        {
          "disturbance": float,
          "e_honest": float,        # mean mismatch rate over trials
          "e_honest_std": float,    # standard deviation
          "n_mean": float,          # mean matched-subset size
          "trials": int,
          "L": int
        }
    """
    mismatch_rates = []
    matched_sizes = []

    for trial in range(trials):
        seed_str = f"honest_{trial}_{secrets.token_hex(8)}"
        k_0, _ = generate_key_set(L)
        true_keys = k_0

        rng = random.Random(seed_str)
        bob_bases = [rng.choice(["X", "Z"]) for _ in range(L)]

        qds = TeleportationQDS(disturbance_prob=disturbance)
        bob_outcomes, _ = qds.execute_session(
            alice_keys=true_keys,
            bob_bases=bob_bases,
            seed_material=seed_str,
            disturbance=disturbance
        )

        m_rate, mismatches, matched_size = compute_mismatch_rate(
            revealed_keys=true_keys,
            bob_bases=bob_bases,
            bob_outcomes=bob_outcomes
        )
        mismatch_rates.append(m_rate)
        matched_sizes.append(matched_size)

    e_honest = float(np.mean(mismatch_rates)) if mismatch_rates else 0.0
    e_honest_std = float(np.std(mismatch_rates)) if mismatch_rates else 0.0
    n_mean = float(np.mean(matched_sizes)) if matched_sizes else 0.0

    return {
        "disturbance": float(disturbance),
        "e_honest": e_honest,
        "e_honest_std": e_honest_std,
        "n_mean": n_mean,
        "trials": int(trials),
        "L": int(L)
    }
