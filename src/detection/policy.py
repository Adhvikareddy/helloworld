"""
Q-SENTINEL Decision Policy.

Defines the QUARANTINE and REJECT thresholds.
"""
import json
import os
from typing import Tuple

class DecisionPolicy:
    def __init__(self, filepath: str = "data/calibration/thresholds.json"):
        self.filepath = filepath
        self.tau_low = 0.05
        self.tau_high = 0.15
        self.version = "uncalibrated"
        self.load_thresholds()

    def load_thresholds(self):
        """Load thresholds from disk."""
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                self.tau_low = data.get("tau_low", self.tau_low)
                self.tau_high = data.get("tau_high", self.tau_high)
                self.version = data.get("version", self.version)

    def save_thresholds(self, tau_low: float, tau_high: float, version: str):
        """Save thresholds to disk."""
        self.tau_low = tau_low
        self.tau_high = tau_high
        self.version = version
        
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w') as f:
            json.dump({
                "tau_low": self.tau_low,
                "tau_high": self.tau_high,
                "version": self.version
            }, f, indent=2)

    def get_thresholds(self) -> Tuple[float, float]:
        return self.tau_low, self.tau_high
        
    def get_version(self) -> str:
        return self.version

    def evaluate(self, D: float) -> str:
        """
        Evaluate a deviation score against the calibrated thresholds.
        
        Returns:
            'ACCEPT' if D <= tau_low
            'QUARANTINE' if tau_low < D <= tau_high
            'REJECT' if D > tau_high
        """
        if D <= self.tau_low:
            return "ACCEPT"
        elif D <= self.tau_high:
            return "QUARANTINE"
        else:
            return "REJECT"

# Global policy instance
global_policy = DecisionPolicy()
