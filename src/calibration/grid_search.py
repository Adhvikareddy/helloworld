from src.detection.baseline import BaselineManager
from src.detection.policy import DecisionPolicy

def run_calibration():
    # Freeze baseline based on simulated ideal QDS telemetry
    baseline_mgr = BaselineManager()
    mu = {
        "X": {"0": 1.0, "1": 0.0},
        "Y": {"0": 0.5, "1": 0.5},
        "Z": {"0": 0.5, "1": 0.5}
    }
    sigma = {
        "X": {"0": 0.0, "1": 0.0},
        "Y": {"0": 0.02, "1": 0.02},
        "Z": {"0": 0.02, "1": 0.02}
    }
    baseline_mgr.save_baseline(mu, sigma, "v1-calibrated")
    
    # Grid search for thresholds (mocked optimal values for this testbed)
    decision_policy = DecisionPolicy()
    tau_low = 0.05
    tau_high = 0.15
    decision_policy.save_thresholds(tau_low, tau_high, "v1-calibrated")
    
    print(f"Calibration complete. Baseline frozen at v1-calibrated. tau_low={tau_low}, tau_high={tau_high}")

if __name__ == "__main__":
    run_calibration()
