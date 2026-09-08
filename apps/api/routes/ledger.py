from fastapi import APIRouter, HTTPException
from src.ledger.hash_chain import global_ledger
from src.ledger.verifier import verify_ledger

router = APIRouter()

@router.get("/verify/{event_id}")
def verify_event(event_id: str):
    event = global_ledger.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.get("/verify-chain")
def verify_chain():
    result = verify_ledger()
    return {"chain_valid": result}
