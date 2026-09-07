from fastapi import APIRouter, HTTPException
from src.ledger.hash_chain import EvidenceLedger
from src.ledger.verifier import LedgerVerifier

router = APIRouter()
ledger = EvidenceLedger()
verifier = LedgerVerifier(ledger)

@router.get("/verify/{event_id}")
def verify_event(event_id: str):
    event = ledger.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.get("/verify-chain")
def verify_chain():
    result = verifier.verify_chain()
    return result
