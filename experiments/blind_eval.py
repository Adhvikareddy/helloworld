"""
Q-SENTINEL Blind Evaluation.

Runs a predeclared population of legitimate and adversarial verification
requests against the LIVE API using frozen thresholds.  Computes standard
detection metrics.

CRITICAL: This script does NOT modify thresholds.  It uses whatever
thresholds are currently frozen.  If run before calibration, the uncalibrated
fallback thresholds will be used — and the results will reflect that.

Usage:
  python -m experiments.blind_eval
  # or via Makefile: make blind
"""
import uuid
import time
import json
import datetime
from attacker.client import get_base_payload, send_verify


def run_blind_evaluation(
    n_legitimate: int = 20,
    n_adversarial: int = 20,
    adversarial_disturbance: float = 0.25,
    shots: int = 1024,
):
    """
    Execute blind evaluation and compute detection metrics.

    Legitimate requests: disturbance=0.0, valid identity, valid nonce.
    Adversarial requests: disturbance=adversarial_disturbance (valid-path forgery).
    """
    print("=" * 60)
    print("  Q-SENTINEL Blind Evaluation")
    print("=" * 60)
    print(f"  Legitimate: {n_legitimate}")
    print(f"  Adversarial: {n_adversarial} (disturbance={adversarial_disturbance})")
    print(f"  Shots: {shots}")
    print()

    TP = 0  # legitimate correctly ACCEPTED
    FN = 0  # legitimate incorrectly NOT accepted
    TN = 0  # adversarial correctly NOT accepted
    FP = 0  # adversarial incorrectly ACCEPTED

    # Phase 1: Legitimate requests
    print(f"[1/2] Running {n_legitimate} legitimate requests...")
    for i in range(n_legitimate):
        payload = get_base_payload(
            shots=shots,
            experiment_id=f"blind_legitimate_{i}",
        )
        raw = send_verify(payload)
        resp = raw["response"]
        decision = resp.get("decision", "ERROR")

        if raw["http_status"] == 200 and decision == "ACCEPT":
            TP += 1
        else:
            FN += 1
            print(f"  ⚠ Legitimate #{i} not accepted: "
                  f"HTTP {raw['http_status']}, decision={decision}")

    # Phase 2: Adversarial requests (valid-path forgery)
    print(f"[2/2] Running {n_adversarial} adversarial requests (disturbance={adversarial_disturbance})...")
    for i in range(n_adversarial):
        payload = get_base_payload(
            shots=shots,
            experiment_id=f"blind_adversarial_{i}",
        )
        payload["disturbance_prob"] = adversarial_disturbance

        raw = send_verify(payload)
        resp = raw["response"]
        decision = resp.get("decision", "ERROR")

        if raw["http_status"] == 403:
            decision = "REJECT"

        if decision == "ACCEPT":
            FP += 1
        else:
            TN += 1

    # Compute metrics
    total = n_legitimate + n_adversarial
    accuracy = (TP + TN) / total if total > 0 else 0.0
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    FAR = FP / (FP + TN) if (FP + TN) > 0 else 0.0
    FRR = FN / (TP + FN) if (TP + FN) > 0 else 0.0
    P_forge = FP / n_adversarial if n_adversarial > 0 else 0.0

    metrics = {
        "TP": TP,
        "TN": TN,
        "FP": FP,
        "FN": FN,
        "Accuracy": round(accuracy, 4),
        "Precision": round(precision, 4),
        "Recall": round(recall, 4),
        "F1": round(f1, 4),
        "FAR (False Accept Rate)": round(FAR, 4),
        "FRR (False Reject Rate)": round(FRR, 4),
        "P_forge_emp": round(P_forge, 4),
    }

    print()
    print("=" * 60)
    print("  Blind Evaluation Results")
    print("=" * 60)
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    print()
    print("  NOTE: These are empirical detector metrics under the tested")
    print("  threat model.  They are NOT formal QDS security bounds.")
    print("=" * 60)

    return metrics


if __name__ == "__main__":
    run_blind_evaluation()
