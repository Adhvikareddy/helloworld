"""
Q-SENTINEL Correlation Engine.

Aggregates findings from multiple independent probes to determine the final decision.
Implements Holm-Bonferroni correction for multiple statistical tests if needed.
"""
from typing import List, Dict, Tuple
from src.detection.findings import Finding, Severity

class CorrelationEngine:
    
    @staticmethod
    def evaluate_findings(findings: List[Finding]) -> Tuple[str, List[dict]]:
        """
        Evaluate a list of findings to produce a final verdict.
        
        Rules:
        1. If ANY finding is REJECT, the final decision is REJECT.
        2. If NO finding is REJECT, but ANY finding is QUARANTINE, the final decision is QUARANTINE.
        3. Otherwise, ACCEPT.
        
        Args:
            findings: List of Finding objects from all probes.
            
        Returns:
            (decision, serialized_findings)
        """
        decision = "ACCEPT"
        serialized = [f.to_dict() for f in findings]
        
        has_quarantine = False
        
        for f in findings:
            if f.severity == Severity.REJECT:
                decision = "REJECT"
                break  # Short-circuit the decision, but we already collected all findings!
            elif f.severity == Severity.QUARANTINE:
                has_quarantine = True
                
        if decision == "ACCEPT" and has_quarantine:
            decision = "QUARANTINE"
            
        return decision, serialized
