"""
ROC Curve & AUC Evaluation (T6).

Generates ROC curve by sweeping the decision threshold tau across the mismatch rate domain
for legitimate signatures versus adversarial key-guessing attacks.
Computes empirical TPR, FPR, and Area Under the ROC Curve (AUC) via trapezoidal integration.
Strict zero-AI/ML: pure mathematical numerical evaluation.

Writes results to experiments/results/roc_curve.csv with columns:
threshold,tpr,fpr
"""
import os
import sys
import csv
import random

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.qds.key_material import generate_key_set
from src.qds.teleportation_qds import TeleportationQDS
from src.qds.verification import compute_mismatch_rate


def run_roc_experiment(n_samples: int = 50, L: int = 90, out_path: str = "experiments/results/roc_curve.csv"):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    # 1. Collect mismatch rates for legitimate population (negative class, low channel disturbance 0.02)
    qds_legit = TeleportationQDS(disturbance_prob=0.02)
    legit_mismatches = []
    for i in range(n_samples):
        k0, _ = generate_key_set(L)
        rng = random.Random(f"roc_legit_{i}")
        bob_bases = [rng.choice(["X", "Y", "Z"]) for _ in range(L)]
        outcomes, _ = qds_legit.execute_session(k0, bob_bases, f"seed_roc_legit_{i}")
        m_rate, _, _ = compute_mismatch_rate(k0, bob_bases, outcomes)
        legit_mismatches.append(m_rate)

    # 2. Collect mismatch rates for adversarial population (positive class, random key guessing)
    qds_clean = TeleportationQDS(disturbance_prob=0.0)
    adv_mismatches = []
    for i in range(n_samples):
        k0, _ = generate_key_set(L)
        rng = random.Random(f"roc_adv_{i}")
        bob_bases = [rng.choice(["X", "Y", "Z"]) for _ in range(L)]
        outcomes, _ = qds_clean.execute_session(k0, bob_bases, f"seed_roc_adv_{i}")
        
        # Adversary guesses random keys
        rng_adv = random.Random(f"roc_guess_{i}")
        guessed_keys = [
            type(k0[0])(basis=rng_adv.choice(["X", "Y", "Z"]), bit=rng_adv.choice([0, 1]))
            for _ in range(L)
        ]
        m_rate, _, _ = compute_mismatch_rate(guessed_keys, bob_bases, outcomes)
        adv_mismatches.append(m_rate)

    # 3. Sweep threshold tau from 0.0 to 0.60
    # Threat is positive class: classified as threat if mismatch_rate > tau
    thresholds = [round(t * 0.02, 3) for t in range(31)]  # 0.00 to 0.60
    roc_points = []
    
    for tau in thresholds:
        tp = sum(1 for m in adv_mismatches if m > tau)
        fn = sum(1 for m in adv_mismatches if m <= tau)
        fp = sum(1 for m in legit_mismatches if m > tau)
        tn = sum(1 for m in legit_mismatches if m <= tau)
        
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        
        roc_points.append({
            "threshold": f"{tau:.3f}",
            "tpr": f"{tpr:.4f}",
            "fpr": f"{fpr:.4f}",
            "_tpr_num": tpr,
            "_fpr_num": fpr
        })

    # 4. Compute AUC using trapezoidal rule sorted by FPR
    # Sort points by FPR ascending
    sorted_pts = sorted(roc_points, key=lambda p: (p["_fpr_num"], p["_tpr_num"]))
    # Add boundary points (0,0) and (1,1) if needed
    pts = [(0.0, 0.0)] + [(p["_fpr_num"], p["_tpr_num"]) for p in sorted_pts] + [(1.0, 1.0)]
    # Deduplicate consecutive points
    clean_pts = []
    for pt in pts:
        if not clean_pts or clean_pts[-1] != pt:
            clean_pts.append(pt)

    auc = 0.0
    for i in range(1, len(clean_pts)):
        dx = clean_pts[i][0] - clean_pts[i-1][0]
        y_avg = (clean_pts[i][1] + clean_pts[i-1][1]) / 2.0
        auc += dx * y_avg
    auc = max(0.0, min(1.0, auc))

    print(f"Computed ROC curve over {len(thresholds)} thresholds.")
    print(f"ROC Area Under Curve (AUC): {auc:.4f}")

    # Write CSV
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["threshold", "tpr", "fpr"])
        writer.writeheader()
        for p in roc_points:
            writer.writerow({
                "threshold": p["threshold"],
                "tpr": p["tpr"],
                "fpr": p["fpr"]
            })

    print(f"Wrote {len(roc_points)} rows to {out_path}")
    return auc


if __name__ == "__main__":
    run_roc_experiment()
