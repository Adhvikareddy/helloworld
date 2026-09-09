"""
Adaptive X-Rotation Experiment (T4 / T6).

Evaluates detection of coherent single-axis X-rotations on the quantum channel:
angles in [0.25, 0.5, 0.75, 1.0] * pi.
Demonstrates mitigation of the v8 evasion attack where fixed |+> state was invisible.
Writes results to experiments/results/adaptive_x.csv.
"""
import os
import sys
import csv
import random

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.qds.key_material import generate_key_set
from src.qds.teleportation_qds import TeleportationQDS
from src.qds.verification import compute_mismatch_rate
from src.detection.probes import StatisticalProbe, TomographyProbe
from src.detection.correlation import CorrelationEngine
from src.detection.policy import global_policy


def run_adaptive_x_experiment(L: int = 150, out_path: str = "experiments/results/adaptive_x.csv"):
    angles = [0.25, 0.5, 0.75, 1.0]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    tau_low, tau_high = global_policy.get_thresholds()
    rows = []
    
    for angle_pi in angles:
        # Run multiple runs per angle for stability
        m_hats = []
        decisions = []
        for rep in range(10):
            k0, _ = generate_key_set(L)
            rng = random.Random(f"adaptive_x_{angle_pi}_{rep}")
            bob_bases = [rng.choice(["X", "Y", "Z"]) for _ in range(L)]
            
            qds = TeleportationQDS(0.0)
            outcomes, _ = qds.execute_session(
                alice_keys=k0,
                bob_bases=bob_bases,
                seed_material=f"adaptive_seed_{angle_pi}_{rep}",
                perturbation="rx_only",
                magnitude=angle_pi
            )
            
            m_hat, mm, n = compute_mismatch_rate(k0, bob_bases, outcomes)
            stat_findings = StatisticalProbe.evaluate(k0, bob_bases, outcomes, tau_low, tau_high)
            tomo_findings = TomographyProbe.evaluate(k0, bob_bases, outcomes)
            dec, _ = CorrelationEngine.evaluate_findings(stat_findings + tomo_findings)
            
            m_hats.append(m_hat)
            decisions.append(dec)
            
        avg_m_hat = sum(m_hats) / len(m_hats)
        # Final decision across runs
        final_dec = "REJECT" if "REJECT" in decisions else ("QUARANTINE" if "QUARANTINE" in decisions else "ACCEPT")
        
        rows.append({
            "angle_pi": f"{angle_pi:.2f}",
            "m_hat": f"{avg_m_hat:.4f}",
            "decision": final_dec
        })
        print(f"angle_pi={angle_pi:.2f}: m_hat={avg_m_hat:.4f}, decision={final_dec}")
        
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["angle_pi", "m_hat", "decision"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    run_adaptive_x_experiment()
