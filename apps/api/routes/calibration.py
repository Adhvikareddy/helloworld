from fastapi import APIRouter
from src.detection.baseline import BaselineManager
from src.detection.policy import DecisionPolicy

router = APIRouter()

baseline_mgr = BaselineManager()
decision_policy = DecisionPolicy()

@router.get("/status")
def get_calibration_status():
    return {
        "baseline_version": baseline_mgr.get_version(),
        "policy_version": decision_policy.get_version(),
        "thresholds": decision_policy.get_thresholds()
    }

@router.post("/reload")
def reload_calibration():
    baseline_mgr.load_baseline()
    decision_policy.load_thresholds()
    return {"status": "reloaded"}
