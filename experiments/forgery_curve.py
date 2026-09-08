"""
Q-SENTINEL Forgery Curve Experiment.

Sweeps disturbance probability from 0.0 to 0.5 in steps and records
the empirical mismatch rate and the theoretical P_forge bound.

Produces a CSV for plotting.
"""
import os
import csv
import time
from src.qds.key_material import generate_key_set
from src.qds.teleportation_qds import TeleportationQDS
from src.detection.forgery_probability import compute_forgery_probability


def run_forgery_curve(
    L: int = 300,
    steps: int = 10,
    repeats: int = 3,
    output_dir: str = "experiments/results"
):
    """
    Sweep disturbance from 0.0 to 0.5 and measure empirical mismatch rate.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "forgery_curve.csv")

    print("=" * 60)
    print("  Q-SENTINEL Forgery Curve Experiment")
    print(f"  L={L}, steps={steps}, repeats={repeats}")
    print("=" * 60)

    results = []

    for step_idx in range(steps + 1):
        disturbance = step_idx * 0.5 / steps
        mismatch_rates = []

        for rep in range(repeats):
            k0, k1 = generate_key_set(L)
            # Bob uses the same bases as Alice's k0 (matched bases)
            bob_bases = [elem.basis for elem in k0]

            qds = TeleportationQDS(disturbance_prob=disturbance)
            bob_outcomes, metadata = qds.execute_session(
                k0, bob_bases, f"forgery_seed_{step_idx}_{rep}"
            )

            mismatches = sum(
                1 for i in range(L) if bob_outcomes[i] != k0[i].bit
            )
            mismatch_rates.append(mismatches / L)

        avg_mismatch = sum(mismatch_rates) / len(mismatch_rates)
        # Theoretical bound at the acceptance threshold
        p_forge_theory = compute_forgery_probability(L, s_a=0.05)

        results.append({
            "disturbance": round(disturbance, 4),
            "avg_mismatch_rate": round(avg_mismatch, 6),
            "p_forge_bound": p_forge_theory,
            "L": L,
        })

        print(f"  d={disturbance:.3f}  mismatch={avg_mismatch:.4f}  "
              f"P_forge={p_forge_theory:.2e}")

    # Write CSV
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults saved to {output_path}")
    return results


if __name__ == "__main__":
    run_forgery_curve()
