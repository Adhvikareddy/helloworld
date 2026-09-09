"""
Noise Sweep Experiment (T1 / T6).
Measures honest baseline mismatch rate across channel disturbance levels:
[0.0, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30]
Calculates analytical thresholds and writes experiments/results/noise_sweep.csv.
"""
import os
import sys
import csv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.calibration.measure_honest import measure_honest_baseline
from src.calibration.analytical import derive_thresholds
from src.detection.policy import global_policy


def run_noise_sweep(trials: int = 15, L: int = 90, out_path: str = "experiments/results/noise_sweep.csv"):
    disturbances = [0.0, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    rows = []
    for d in disturbances:
        r = measure_honest_baseline(disturbance=d, trials=trials, L=L)
        n = int(round(r["n_mean"]))
        e_honest = r["e_honest"]
        
        tau_low = derive_thresholds(n, e_honest, alpha=1e-4)
        tau_high = derive_thresholds(n, e_honest, alpha=1e-6)
        if tau_high <= tau_low:
            tau_high = min(1.0, tau_low + 1.0 / max(n, 1))
            
        rows.append({
            "disturbance": f"{d:.4f}",
            "e_honest": f"{e_honest:.4f}",
            "e_honest_std": f"{r['e_honest_std']:.4f}",
            "n_mean": f"{r['n_mean']:.2f}",
            "tau_low": f"{tau_low:.4f}",
            "tau_high": f"{tau_high:.4f}"
        })
        print(f"Disturbance {d:.2f}: e_honest={e_honest:.4f} (std={r['e_honest_std']:.4f}), n_mean={r['n_mean']:.1f}, tau_low={tau_low:.4f}, tau_high={tau_high:.4f}")
        
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["disturbance", "e_honest", "e_honest_std", "n_mean", "tau_low", "tau_high"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")

    # Ensure operating thresholds are saved for default 0.02 disturbance
    default_res = measure_honest_baseline(disturbance=0.02, trials=trials, L=L)
    global_policy.calibrate(n=int(round(default_res["n_mean"])), p_err_honest=default_res["e_honest"])


if __name__ == "__main__":
    run_noise_sweep()
