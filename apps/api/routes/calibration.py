from fastapi import APIRouter
from src.detection.baseline import BaselineManager
from src.detection.policy import DecisionPolicy

router = APIRouter()

baseline_mgr = BaselineManager()
decision_policy = DecisionPolicy()

@router.get("/status")
def get_calibration_status():
    tau_low, tau_high = decision_policy.get_thresholds()
    return {
        "baseline_version": baseline_mgr.get_version(),
        "policy_version": decision_policy.get_version(),
        "thresholds": {"tau_low": tau_low, "tau_high": tau_high},
        "threshold_list": [tau_low, tau_high],
        "baseline": {
            "X": 1.0,
            "Y": 0.5,
            "Z": 0.5,
            "mu": baseline_mgr.get_mu_dict()
        }
    }

@router.post("/reload")
def reload_calibration():
    baseline_mgr.load_baseline()
    decision_policy.load_thresholds()
    return {"status": "reloaded"}
