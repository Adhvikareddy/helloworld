from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import time

from src.security.identity import global_pqc_identity
from src.keyvault import global_keyvault
from src.keyvault.session_store import global_session_store

router = APIRouter()

class RevealRequest(BaseModel):
    session_id: str = Field(..., max_length=128)
    signer_id: str = Field(..., max_length=64)
    message_bit: int = Field(..., ge=0, le=1)
    nonce: str = Field(..., max_length=128)
    timestamp: float = Field(..., description="Unix timestamp")
    signature: str = Field(..., max_length=8192)

class RevealResponse(BaseModel):
    session_id: str
    message_bit: int
    revealed_keys: List[Dict[str, Any]]

@router.post("/reveal", response_model=RevealResponse)
def reveal_keys(req: RevealRequest, request: Request):
    payload_dict = req.model_dump(exclude={"signature"})
    if not global_pqc_identity.verify_request_signature(req.signer_id, payload_dict, req.signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    session = global_session_store.get_session_record(req.session_id)
    if not session:
        raise HTTPException(status_code=440, detail=f"Session {req.session_id} not found in store")

    try:
        keys = global_keyvault.reveal_keys(req.session_id, req.signer_id, req.message_bit)
        keys_dict = [{"bit_index": idx, "basis": k.basis, "bit_value": k.bit} for idx, k in enumerate(keys)]
        return RevealResponse(
            session_id=req.session_id,
            message_bit=req.message_bit,
            revealed_keys=keys_dict
        )
    except ValueError as e:

        raise HTTPException(status_code=400, detail=str(e))
