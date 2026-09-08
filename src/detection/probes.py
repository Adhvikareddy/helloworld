"""
Q-SENTINEL Detection Probes.

Independent probes that evaluate different dimensions of the request.
Instead of raising exceptions (short-circuiting), they return Findings.
"""
from typing import List, Dict, Any, Optional
from src.detection.findings import Finding, Severity
from src.qds.verification import compute_mismatch_rate
from src.qds.key_material import QuantumKeyElement

class AuthenticationProbe:
    """Evaluates identity and authorization."""
    
    @staticmethod
    def evaluate(is_identity_valid: bool, is_authorized: bool, signer_id: str, verifier_id: str) -> List[Finding]:
        findings = []
        if not is_identity_valid:
            findings.append(Finding(
                detector_name="IdentityGuard",
                severity=Severity.REJECT,
                description="Invalid identity binding. Signature failed verification.",
                metrics={"signer_id": signer_id}
            ))
        if not is_authorized:
            findings.append(Finding(
                detector_name="AuthorizationGuard",
                severity=Severity.REJECT,
                description="Verifier is not authorized to invoke this endpoint.",
                metrics={"verifier_id": verifier_id}
            ))
        return findings

class FreshnessProbe:
    """Evaluates nonces and timestamps."""
    
    @staticmethod
    def evaluate(is_timestamp_valid: bool, is_replay: bool, nonce: str, session_id: str) -> List[Finding]:
        findings = []
        if not is_timestamp_valid:
            findings.append(Finding(
                detector_name="TimestampGuard",
                severity=Severity.REJECT,
                description="Request timestamp is stale or too far in the future.",
                metrics={"session_id": session_id}
            ))
        if is_replay:
            findings.append(Finding(
                detector_name="ReplayGuard",
                severity=Severity.REJECT,
                description="Replay detected. Nonce has already been used for this session.",
                metrics={"nonce": nonce, "session_id": session_id}
            ))
        return findings

class StatisticalProbe:
    """Evaluates the quantum measurement mismatch rate against analytical bounds."""
    
    @staticmethod
    def evaluate(
        revealed_keys: List[QuantumKeyElement],
        bob_bases: List[str],
        bob_outcomes: List[int],
        tau_low: float,
        tau_high: float
    ) -> List[Finding]:
        
        mismatch_rate, mismatches, n = compute_mismatch_rate(revealed_keys, bob_bases, bob_outcomes)
        
        if n == 0:
            return [Finding(
                detector_name="QuantumDetector",
                severity=Severity.REJECT,
                description="No matching bases found. Cannot verify signature.",
                metrics={"mismatch_rate": 1.0, "n": 0}
            )]
            
        metrics = {
            "mismatch_rate": mismatch_rate,
            "mismatches": mismatches,
            "matched_subset_size": n,
            "tau_low": tau_low,
            "tau_high": tau_high
        }
        
        if mismatch_rate <= tau_low:
            severity = Severity.INFO
            desc = "Mismatch rate within legitimate bounds."
        elif mismatch_rate <= tau_high:
            severity = Severity.QUARANTINE
            desc = "Elevated mismatch rate. Possible channel disturbance."
        else:
            severity = Severity.REJECT
            desc = "Mismatch rate exceeds high threshold. Forgery detected."
            
        return [Finding(
            detector_name="QuantumDetector",
            severity=severity,
            description=desc,
            metrics=metrics
        )]


class TomographyProbe:
    """
    D1 Differentiator: Channel Tomography for Attack Attribution.
    
    Analyzes per-basis mismatch rates to classify the attack type
    (depolarizing noise, coherent X/Y/Z rotation, or clean channel).
    """
    
    @staticmethod
    def evaluate(
        revealed_keys: List[QuantumKeyElement],
        bob_bases: List[str],
        bob_outcomes: List[int],
    ) -> List[Finding]:
        from src.detection.tomography import compute_basis_mismatch_rates, classify_attack
        
        basis_rates = compute_basis_mismatch_rates(revealed_keys, bob_bases, bob_outcomes)
        classification = classify_attack(basis_rates)
        
        attack_type = classification["classification"]
        confidence = classification["confidence"]
        
        if attack_type == "INSUFFICIENT_DATA":
            return []  # Not enough data to classify
        
        if attack_type == "CLEAN":
            severity = Severity.INFO
        elif attack_type == "DEPOLARIZING":
            severity = Severity.QUARANTINE
        else:
            severity = Severity.QUARANTINE  # Coherent attacks get quarantine; the statistical probe handles reject
        
        return [Finding(
            detector_name="ChannelTomography",
            severity=severity,
            description=classification["description"],
            metrics={
                "attack_type": attack_type,
                "confidence": confidence,
                "basis_rates": classification["basis_rates"],
            }
        )]
