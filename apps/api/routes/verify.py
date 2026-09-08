from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time

from src.security.identity import global_pqc_identity
from src.security.nonce import global_nonce_guard, TimestampGuard
from src.security.rate_limit import global_rate_limiter
from src.qds.key_material import QuantumKeyElement
from src.keyvault.session_store import global_session_store
from src.detection.probes import AuthenticationProbe, FreshnessProbe, StatisticalProbe, TomographyProbe
from src.detection.correlation import CorrelationEngine
from src.detection.policy import global_policy
from src.ledger.hash_chain import global_ledger
from src.detection.findings import Finding, Severity

router = APIRouter()

class KeyElementSchema(BaseModel):
    bit_index: int
    basis: str
    bit_value: int

class VerifyRequest(BaseModel):
    session_id: str = Field(..., max_length=128, description="The key distribution session ID")
    signer_id: str = Field(..., max_length=64, description="Identity of the signer (Alice)")
    verifier_id: str = Field(..., max_length=64, description="Identity of the verifier (Bob or Charlie)")
    nonce: str = Field(..., max_length=128, description="Unique nonce to prevent replay")
    timestamp: float = Field(..., description="Unix timestamp of the request")
    message_bit: int = Field(..., ge=0, le=1, description="The message bit being signed (0 or 1)")
    revealed_keys: List[KeyElementSchema] = Field(..., description="Alice's revealed classical keys for message_bit")
    signature: str = Field(..., max_length=8192, description="ML-DSA-65 signature of request payload")

class VerifyResponse(BaseModel):
    decision: str
    findings: List[Dict[str, Any]]
    evidence_id: str
    latency_ms: float
    calibration_status: str

@router.post("/verify", response_model=VerifyResponse)
def verify_qds(req: VerifyRequest, request: Request):
    start_time = time.time()
    
    # 1. Rate Limiting
    client_ip = request.client.host if request.client else "unknown"
    global_rate_limiter.check_rate_limit(client_ip)
    
    # Fail-closed on missing calibration
    if global_policy.get_version() == "uncalibrated":
        raise HTTPException(
            status_code=503,
            detail="System uncalibrated. Refusing to process verification requests."
        )
        
    all_findings = []
    
    # 2. Extract payload for signature verification
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

    # Check for session double consumption per verifier in SQLite
    if global_session_store.is_consumed(req.session_id, req.verifier_id):
        all_findings.append(Finding(
            detector_name="DoubleConsumptionGuard",
            severity=Severity.REJECT,
            description=f"Session {req.session_id} has already been verified by {req.verifier_id}.",
            metrics={"session_id": req.session_id, "verifier_id": req.verifier_id}
        ))
    else:
        global_session_store.mark_consumed(req.session_id, req.verifier_id, start_time)

    # 5. Look up pre-distributed verifier session outcomes
    v_data = global_session_store.get_verifier_outcomes(req.session_id, req.verifier_id)
    if not v_data:
        all_findings.append(Finding(
            detector_name="SessionStore",
            severity=Severity.REJECT,
            description=f"No pre-distributed states found for session {req.session_id} and verifier {req.verifier_id}.",
            metrics={}
        ))
    else:
        bob_bases, bob_outcomes = v_data
        alice_keys = [
            QuantumKeyElement(basis=k.basis, bit=k.bit_value)
            for k in req.revealed_keys
        ]

        
        # Statistical evaluation (L2)
        tau_low, tau_high = global_policy.get_thresholds()
        stat_findings = StatisticalProbe.evaluate(
            alice_keys, bob_bases, bob_outcomes, tau_low, tau_high
        )
        all_findings.extend(stat_findings)
        
        # Channel Tomography for attack attribution (L2)
        tomography_findings = TomographyProbe.evaluate(
            alice_keys, bob_bases, bob_outcomes
        )
        all_findings.extend(tomography_findings)

    # 6. Correlation Engine
    decision, serialized_findings = CorrelationEngine.evaluate_findings(all_findings)
    
    # 7. Evidence Ledger (L4)
    event_data = {
        "timestamp": time.time(),
        "session_id": req.session_id,
        "signer_id": req.signer_id,
        "verifier_id": req.verifier_id,
        "decision": decision,
        "findings": serialized_findings,
    }
    
    event_id = global_ledger.record_event(event_data)
    
    # 8. Constant-time latency calculation without fixed sleep
    latency = (time.time() - start_time) * 1000.0
    
    return VerifyResponse(
        decision=decision,
        findings=serialized_findings,
        evidence_id=event_id,
        latency_ms=latency,
        calibration_status=global_policy.get_version()
    )

