import json
import os

class DecisionPolicy:
    """
    Evaluates ACCEPT / QUARANTINE / REJECT based on deterministic thresholds.
    """
    def __init__(self, filepath="data/thresholds.json"):
        self.filepath = filepath
        self.thresholds = None
        self.load_thresholds()

    def load_thresholds(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                self.thresholds = json.load(f)
        else:
            self.thresholds = {
                "tau_low": 0.05,
                "tau_high": 0.15,
                "version": "uncalibrated"
            }

    def save_thresholds(self, tau_low, tau_high, version):
        self.thresholds = {"tau_low": tau_low, "tau_high": tau_high, "version": version}
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w') as f:
            json.dump(self.thresholds, f)

    def evaluate(self, D: float) -> str:
        tau_low = self.thresholds["tau_low"]
        tau_high = self.thresholds["tau_high"]
        if D <= tau_low:
            return "ACCEPT"
        elif tau_low < D <= tau_high:
            return "QUARANTINE"
        else:
            return "REJECT"

    def get_version(self) -> str:
        return self.thresholds.get("version", "unknown")
        
    def get_thresholds(self) -> dict:
        return self.thresholds
