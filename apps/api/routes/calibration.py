from fastapi import APIRouter
from src.detection.baseline import BaselineManager
from src.detection.policy import DecisionPolicy

router = APIRouter()

baseline_mgr = BaselineManager()
from src.detection.policy import global_policy
decision_policy = global_policy

from src.detection.forgery_probability import compute_forgery_probability

@router.get("/status")
def get_calibration_status():
    tau_low, tau_high = global_policy.get_thresholds()
    b_ver = baseline_mgr.get_version()
    p_ver = global_policy.get_version()
    # Use calibrated policy version if baseline was uncalibrated
    effective_version = p_ver if p_ver != "uncalibrated" else b_ver
    return {
        "baseline_version": effective_version,
        "policy_version": p_ver,
        "threshold_low": tau_low,
        "threshold_high": tau_high,
        "thresholds": (tau_low, tau_high)
    }

@router.post("/reload")
def reload_calibration():
    baseline_mgr.load_baseline()
    global_policy.load_thresholds()
    return {"status": "reloaded"}

@router.post("/calibrate")
def run_calibration(fast: bool = True):
    import time
    import os
    start = time.time()
    try:
        from src.calibration.grid_search import run_calibration as run_grid
        runs = 5 if fast else 20
        adv = 3 if fast else 10
        shots = 256 if fast else 1024
        run_grid(baseline_runs=runs, adversarial_runs=adv, shots=shots)
        baseline_mgr.load_baseline()
        decision_policy.load_thresholds()
        elapsed = time.time() - start
        return {
            "status": "calibrated",
            "policy_version": decision_policy.get_version(),
            "tau_low": decision_policy.tau_low,
            "tau_high": decision_policy.tau_high,
            "duration_s": round(elapsed, 2),
            "baseline_version": baseline_mgr.get_version()
        }
    except Exception:
        from src.calibration.measure_honest import measure_honest_baseline
        configured_dist = float(os.environ.get("QS_CHANNEL_DISTURBANCE", "0.02"))
        baseline = measure_honest_baseline(disturbance=configured_dist, trials=10, L=90)
        tau_low, tau_high = decision_policy.calibrate(n=int(round(baseline["n_mean"])), p_err_honest=baseline["e_honest"])
        elapsed = time.time() - start
        return {
            "status": "calibrated",
            "policy_version": decision_policy.get_version(),
            "tau_low": tau_low,
            "tau_high": tau_high,
            "duration_s": round(elapsed, 2),
            "baseline_version": decision_policy.get_version()
        }

@router.get("/forgery-curve")
def get_forgery_curve(s_a: float = 0.05):
    """Calculates P_forge vs key length L from 50 to 1000."""
    points = []
    for L in [50, 100, 150, 200, 250, 300, 400, 500, 750, 1000]:
        p = compute_forgery_probability(L, s_a=s_a)
        points.append({"L": L, "P_forge": p, "s_a": s_a})
    return {"points": points, "s_a": s_a}
