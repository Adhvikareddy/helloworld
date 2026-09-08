from fastapi import APIRouter, HTTPException, Request, Depends, Header
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time

from src.security.identity import global_pqc_identity
from src.security.nonce import global_nonce_guard, TimestampGuard
from src.security.rate_limit import global_rate_limiter
from src.qds.teleportation_qds import TeleportationQDS
from src.qds.key_material import QuantumKeyElement
from src.keyvault import global_keyvault
from src.detection.probes import AuthenticationProbe, FreshnessProbe, StatisticalProbe, TomographyProbe
from src.detection.correlation import CorrelationEngine
from src.detection.policy import global_policy
from src.ledger.hash_chain import global_ledger

router = APIRouter()

class VerifyRequest(BaseModel):
    session_id: str = Field(..., max_length=128, description="The key distribution session ID")
    signer_id: str = Field(..., max_length=64, description="Identity of the signer")
    verifier_id: str = Field(..., max_length=64, description="Identity of the verifier")
    nonce: str = Field(..., max_length=128, description="Unique nonce to prevent replay")
    timestamp: float = Field(..., description="Unix timestamp of the request")
    
    message_bit: int = Field(..., ge=0, le=1, description="The message bit being signed (0 or 1)")
    measurement_bases: List[str] = Field(..., max_length=10000, description="Bob's chosen measurement bases")
    
    signature: str = Field(..., max_length=8192, description="ML-DSA-65 signature of the request payload")
    
    experiment_id: Optional[str] = Field(None, max_length=64)

class VerifyResponse(BaseModel):
    decision: str
    findings: List[Dict[str, Any]]
    evidence_id: str
    latency_ms: float
    calibration_status: str

@router.post("/verify", response_model=VerifyResponse)
def verify_qds(
    req: VerifyRequest,
    request: Request,
    x_testbed_disturbance: float = Header(0.0, ge=0.0, le=1.0)
):
    start_time = time.time()
    
    # 1. Rate Limiting
    client_ip = request.client.host if request.client else "unknown"
    global_rate_limiter.check_rate_limit(client_ip)
    
    # Fail-closed on missing calibration (F4 fix)
    if global_policy.get_version() == "uncalibrated":
        raise HTTPException(
            status_code=503,
            detail="System uncalibrated. Refusing to process verification requests."
        )
        
    all_findings = []
    
    # 2. Extract payload for signature verification (exclude the signature itself)
    payload_dict = req.model_dump(exclude={"signature"})
    
    # 3. Authentication Probe (L3)
    is_identity_valid = global_pqc_identity.verify_request_signature(
        req.signer_id, payload_dict, req.signature
    )
    is_authorized = global_pqc_identity.is_verifier_authorized(req.verifier_id)
    
    auth_findings = AuthenticationProbe.evaluate(
        is_identity_valid, is_authorized, req.signer_id, req.verifier_id
    )
    all_findings.extend(auth_findings)
    
    # 4. Freshness Probe (L3)
    is_timestamp_valid = TimestampGuard.is_valid(req.timestamp)
    is_fresh = global_nonce_guard.is_fresh(req.nonce, req.session_id)
    
    freshness_findings = FreshnessProbe.evaluate(
        is_timestamp_valid, not is_fresh, req.nonce, req.session_id
    )
    all_findings.extend(freshness_findings)
    
    # 5. Quantum Protocol Execution (L1) & Statistical Probe (L2)
    # We only run the quantum circuits if we have a valid session to avoid crashing on missing keys
    session = global_keyvault.get_session_for_distribution(req.session_id)
    if not session:
        # If the session doesn't exist, we can't do the quantum part.
        from src.detection.findings import Finding, Severity
        all_findings.append(Finding(
            detector_name="KeyVault",
            severity=Severity.REJECT,
            description=f"Session {req.session_id} not found in keyvault.",
            metrics={}
        ))
    else:
        try:
            # Reveal keys for the requested message bit (marks session as used)
            alice_keys = global_keyvault.reveal_keys(req.session_id, req.signer_id, req.message_bit)
            
            # Execute the quantum network transmission
            qds_core = TeleportationQDS(disturbance_prob=x_testbed_disturbance)
            seed_material = f"{req.session_id}:{req.nonce}"
            
            pure_x = req.experiment_id == "test_pure_x_rotation"
            
            bob_outcomes, metadata = qds_core.execute_session(
                alice_keys, req.measurement_bases, seed_material,
                pure_x_rotation=pure_x, disturbance=x_testbed_disturbance
            )
            
            # Statistical evaluation
            tau_low, tau_high = global_policy.get_thresholds()
            stat_findings = StatisticalProbe.evaluate(
                alice_keys, req.measurement_bases, bob_outcomes, tau_low, tau_high
            )
            all_findings.extend(stat_findings)
            
            # D1: Channel Tomography for attack attribution
            tomography_findings = TomographyProbe.evaluate(
                alice_keys, req.measurement_bases, bob_outcomes
            )
            all_findings.extend(tomography_findings)
            
        except Exception as e:
            from src.detection.findings import Finding, Severity
            all_findings.append(Finding(
                detector_name="QuantumDetector",
                severity=Severity.REJECT,
                description=f"Quantum execution failed: {str(e)}",
                metrics={}
            ))
            
    # 6. Correlation Engine (Holistic Decision)
    decision, serialized_findings = CorrelationEngine.evaluate_findings(all_findings)
    
    # 7. Evidence Ledger (L4)
    event_data = {
        "timestamp": time.time(),
        "session_id": req.session_id,
        "signer_id": req.signer_id,
        "verifier_id": req.verifier_id,
        "decision": decision,
        "findings": serialized_findings,
        "experiment_id": req.experiment_id
    }
    
    event_id = global_ledger.record_event(event_data)
    
    # 8. Side Channel Protection (L3)
    # Mask execution time differences (constant-time envelope)
    # E.g. authentication failures are fast, quantum execution is slow.
    elapsed = time.time() - start_time
    target_latency = 2.0  # seconds
    if elapsed < target_latency:
        time.sleep(target_latency - elapsed)
        
    # Response Tiering (only return detailed findings if the decision is ACCEPT or QUARANTINE, 
    # or if the verifier is a high-entitlement user).
    # For a REJECT on auth, we don't return internal state.
    returned_findings = []
    if decision != "REJECT" or req.verifier_id in ["auditor", "admin"]:
        returned_findings = serialized_findings
    else:
        # Just give a generic reason
        from src.detection.findings import Finding, Severity
        returned_findings = [Finding(
            detector_name="Gateway",
            severity=Severity.REJECT,
            description="Request rejected by policy.",
            metrics={}
        ).to_dict()]
        
    latency = (time.time() - start_time) * 1000
    
    return VerifyResponse(
        decision=decision,
        findings=returned_findings,
        evidence_id=event_id,
        latency_ms=latency,
        calibration_status=global_policy.get_version()
    )
