import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import json
import time
from attacker.blind_trial import run_blind_batch, execute_blind_trial, TRIAL_TYPES

def main():
    print("=== Executing 8 Sample Blind Trials (1 per type) ===")
    for t in TRIAL_TYPES:
        res = execute_blind_trial(t)
        gt = res["ground_truth"]
        det = res["detector_result"]
        ev = res["evaluation"]
        print(f"{t:<22} | Exp: {gt['expected_verdict']:<10} | Act: {det['actual_decision']:<10} | Layer: {det['primary_layer']:<8} | Class: {ev['confusion_class']}")

    print("\n=== Executing 100 Autonomous Blind Trials ===")
    t0 = time.time()
    batch_res = run_blind_batch(100)
    elapsed = time.time() - t0
    
    print(f"Completed 100 trials in {elapsed:.2f}s")
    print("\nConfusion Matrix:")
    print(json.dumps(batch_res["confusion_matrix"], indent=2))
    print("\nMetrics:")
    print(json.dumps(batch_res["metrics"], indent=2))
    print("\nType Breakdown:")
    print(json.dumps(batch_res["type_breakdown"], indent=2))

if __name__ == "__main__":
    main()
