import json
import os

class BaselineManager:
    """
    Manages the frozen legitimate measurement baseline for the statistical detector.
    """
    def __init__(self, filepath=None):
        if filepath is None:
            if os.path.exists("data/calibration/baseline.json"):
                self.filepath = "data/calibration/baseline.json"
            elif os.path.exists("data/baseline.json"):
                self.filepath = "data/baseline.json"
            else:
                self.filepath = "data/calibration/baseline.json"
        else:
            self.filepath = filepath
        self.baseline = None
        self.load_baseline()

    def load_baseline(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                self.baseline = json.load(f)
        else:
            # Fallback uniform/ideal baseline if uncalibrated
            self.baseline = {
                "mu": {
                    "X": {"0": 1.0, "1": 0.0},
                    "Y": {"0": 0.5, "1": 0.5},
                    "Z": {"0": 0.5, "1": 0.5}
                },
                "sigma": {},
                "version": "uncalibrated"
            }
            
    def save_baseline(self, mu, sigma, version):
        self.baseline = {"mu": mu, "sigma": sigma, "version": version}
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w') as f:
            json.dump(self.baseline, f)
            
    def get_mu_dict(self) -> dict:
        return self.baseline["mu"]
    
    def get_version(self) -> str:
        return self.baseline.get("version", "unknown")
