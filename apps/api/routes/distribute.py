from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time

from src.security.identity import global_pqc_identity
from src.security.nonce import global_nonce_guard, TimestampGuard
from src.security.rate_limit import global_rate_limiter
from src.qds.teleportation_qds import TeleportationQDS
from src.qds.key_material import QuantumKeyElement, generate_key_set
from src.keyvault import global_keyvault
from src.keyvault.session_store import global_session_store


router = APIRouter()

class DistributeRequest(BaseModel):
    session_id: str = Field(..., max_length=128, description="Unique distribution session ID")
    signer_id: str = Field(..., max_length=64, description="Identity of the signer (Alice)")
    verifiers: List[str] = Field(..., min_items=1, description="List of verifier IDs (e.g. ['bob', 'charlie'])")
    L: int = Field(100, ge=10, le=10000, description="Number of quantum key elements per bit")
    nonce: str = Field(..., max_length=128, description="Unique nonce to prevent replay")
    timestamp: float = Field(..., description="Unix timestamp of the request")
    signature: str = Field(..., max_length=8192, description="ML-DSA-65 signature of request payload")
    disturbance: Optional[float] = Field(0.0, ge=0.0, le=1.0, description="Physical channel disturbance rate during distribution")

class DistributeResponse(BaseModel):
    status: str
    session_id: str
    distributed_verifiers: List[str]
    elements_per_verifier: int

@router.post("/distribute", response_model=DistributeResponse)
def distribute_qds(req: DistributeRequest, request: Request):
    # 1. Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    global_rate_limiter.check_rate_limit(client_ip)

    # 2. Extract payload & verify ML-DSA-65 signature
    payload_dict = req.model_dump(exclude={"signature"})
    if not global_pqc_identity.verify_request_signature(req.signer_id, payload_dict, req.signature):
        raise HTTPException(status_code=401, detail="Invalid signature for signer")

    # 3. Check freshness
    if not TimestampGuard.is_valid(req.timestamp):
        raise HTTPException(status_code=400, detail="Stale timestamp")
    if not global_nonce_guard.is_fresh(req.nonce, req.session_id):
        raise HTTPException(status_code=409, detail="Replay attack detected: Nonce already used")

    # 4. Generate keys & simulate distribution channel transmission
    session = global_keyvault.create_session(req.signer_id, req.L)
    # Ensure the session_id matches requested session_id
    global_keyvault._sessions.pop(session.session_id, None)
    session.session_id = req.session_id
    global_keyvault._sessions[req.session_id] = session

    created_at = time.time()
    global_session_store.create_session_record(req.session_id, req.signer_id, req.L, created_at)

    qds_core = TeleportationQDS(disturbance_prob=req.disturbance or 0.0)


    for v_id in req.verifiers:
        # Generate Bob's measurement bases deterministically or randomly for simulation
        import random
        rng = random.Random(f"{req.session_id}:{v_id}")
        bob_bases = [rng.choice(["X", "Z"]) for _ in range(req.L)]
        seed_material = f"{req.session_id}:{v_id}"
        
        # Teleport bit states to verifier v_id over noisy channel
        # We perform teleportation for message_bit=0 material (or combined set)
        bob_outcomes, _ = qds_core.execute_session(
            session.k_0, bob_bases, seed_material, disturbance=req.disturbance or 0.0
        )
        global_session_store.store_verifier_outcomes(req.session_id, v_id, bob_bases, bob_outcomes)

    return DistributeResponse(
        status="DISTRIBUTED",
        session_id=req.session_id,
        distributed_verifiers=req.verifiers,
        elements_per_verifier=req.L
    )
