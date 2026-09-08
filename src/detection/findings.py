"""
Q-SENTINEL Finding Architecture.

Defines the structured format for detection findings. 
A single request generates multiple independent findings which are then correlated.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum

class Severity(Enum):
    INFO = "INFO"             # Normal operation, baseline metrics
    QUARANTINE = "QUARANTINE" # Suspicious, hold for manual review / dispute resolution
    REJECT = "REJECT"         # Known bad, drop immediately

@dataclass
class Finding:
    """
    A single independent observation from a detection probe.
    """
    detector_name: str
    severity: Severity
    description: str
    metrics: Dict[str, Any]
    
    def is_blocking(self) -> bool:
        """Return True if this finding should block the request from proceeding."""
        return self.severity == Severity.REJECT
        
    def to_dict(self) -> dict:
        return {
            "detector": self.detector_name,
            "severity": self.severity.value,
            "description": self.description,
            "metrics": self.metrics
        }
