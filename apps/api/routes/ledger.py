from fastapi import APIRouter, HTTPException, Query
from src.ledger.hash_chain import global_ledger
from src.ledger.verifier import verify_ledger, audit_ledger

router = APIRouter()

@router.get("/events")
def list_events(limit: int = Query(50, ge=1, le=500)):
    """Return recent events from the SQLite evidence ledger."""
    events = global_ledger.get_recent_events(limit=limit)
    return {"events": events, "total": len(events)}

@router.get("/verify/{event_id}")
def verify_event(event_id: str):
    event = global_ledger.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.get("/verify-chain")
def verify_chain():
    result = audit_ledger()
    return result
