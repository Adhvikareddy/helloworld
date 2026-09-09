"""
Q-SENTINEL Decision Policy.

Defines the QUARANTINE and REJECT thresholds.
"""
import json
import os
from typing import Tuple
from src.calibration.analytical import derive_thresholds

class DecisionPolicy:
    def __init__(self, filepath: str = "data/calibration/thresholds.json"):
        self.filepath = filepath
        self.tau_low = 0.05
        self.tau_high = 0.15
        self.version = "uncalibrated"
        self.provenance = {}
        self.load_thresholds()

    def load_thresholds(self):
        """Load thresholds from disk."""
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                self.tau_low = data.get("tau_low", self.tau_low)
                self.tau_high = data.get("tau_high", self.tau_high)
                self.version = data.get("version", self.version)
                self.provenance = data.get("provenance", {})

    def save_thresholds(self, tau_low: float, tau_high: float, version: str, provenance: dict = None):
        """Save thresholds to disk."""
        self.tau_low = tau_low
        self.tau_high = tau_high
        self.version = version
        self.provenance = provenance or {}
        
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w') as f:
            data = {
                "tau_low": self.tau_low,
                "tau_high": self.tau_high,
                "version": self.version
            }
            if self.provenance:
                data["provenance"] = self.provenance
            json.dump(data, f, indent=2)

    def calibrate(self, n: int, p_err_honest: float, alpha: float = 1e-4,
                  version: str = "analytical_v92"):
        """Calibrate thresholds analytically from a MEASURED honest baseline."""
        tau_low = derive_thresholds(n, p_err_honest, alpha)
        tau_high = derive_thresholds(n, p_err_honest, alpha / 100.0)
        if tau_high <= tau_low:
            tau_high = min(1.0, tau_low + 1.0 / max(n, 1))
        self.save_thresholds(tau_low, tau_high, version,
                             provenance={"n": n, "e_honest": p_err_honest,
                                         "alpha": alpha, "derivation": "binom.ppf"})
        return tau_low, tau_high

    def get_thresholds(self) -> Tuple[float, float]:
        return self.tau_low, self.tau_high
        
    def get_version(self) -> str:
        return self.version

    def evaluate(self, D: float) -> str:
        if D <= self.tau_low:
            return "ACCEPT"
        elif D <= self.tau_high:
            return "QUARANTINE"
        else:
            return "REJECT"

# Global policy instance
global_policy = DecisionPolicy()

