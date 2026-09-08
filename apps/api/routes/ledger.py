from fastapi import APIRouter, HTTPException
from src.ledger.hash_chain import global_ledger
from src.ledger.verifier import verify_ledger

router = APIRouter()

import sqlite3
import json

@router.get("/verify/{event_id}")
def verify_event(event_id: str):
    event = global_ledger.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

from src.ledger.hash_chain import LEDGER_SECRET
import hmac
import hashlib

@router.get("/verify-chain")
def verify_chain():
    try:
        with sqlite3.connect(global_ledger.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM evidence ORDER BY seq_num ASC")
            rows = cursor.fetchall()
            if not rows:
                return {"chain_valid": True, "total_records": 0}
            genesis = rows[0]
            if genesis['event_id'] != 'genesis':
                return {"chain_valid": False, "broken_at": 0, "reason": "Genesis block tampered"}
            expected_sig = hmac.new(LEDGER_SECRET, genesis['current_hash'].encode('utf-8'), hashlib.sha256).hexdigest()
            if genesis['signature'] != expected_sig:
                return {"chain_valid": False, "broken_at": 0, "reason": "Genesis signature invalid"}
            previous_hash = genesis['current_hash']
            for i in range(1, len(rows)):
                row = rows[i]
                if row['previous_hash'] != previous_hash:
                    return {"chain_valid": False, "broken_at": row['seq_num'], "reason": "Linkage broken"}
                canonical_fields = {
                    "seq_num": row['seq_num'],
                    "event_id": row['event_id'],
                    "timestamp": row['timestamp'],
                    "session_id": row['session_id'],
                    "signer_id": row['signer_id'],
                    "verifier_id": row['verifier_id'],
                    "decision": row['decision'],
                    "findings": row['findings'],
                    "experiment_id": row['experiment_id']
                }
                canonical_event = json.dumps(canonical_fields, sort_keys=True).encode('utf-8')
                hash_input = previous_hash.encode('utf-8') + canonical_event
                expected_hash = hashlib.sha256(hash_input).hexdigest()
                if row['current_hash'] != expected_hash:
                    return {"chain_valid": False, "broken_at": row['seq_num'], "reason": f"Hash mismatch at seq_num {row['seq_num']}"}
                expected_sig = hmac.new(LEDGER_SECRET, row['current_hash'].encode('utf-8'), hashlib.sha256).hexdigest()
                if row['signature'] != expected_sig:
                    return {"chain_valid": False, "broken_at": row['seq_num'], "reason": f"HMAC signature mismatch at seq_num {row['seq_num']}"}
                previous_hash = row['current_hash']
            return {"chain_valid": True, "total_records": len(rows)}
    except Exception as e:
        return {"chain_valid": False, "error": str(e)}

@router.get("/events")
def get_recent_events(limit: int = 50):
    """Retrieve recent evidence blocks for live hash chain visualization."""
    try:
        with sqlite3.connect(global_ledger.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM evidence ORDER BY seq_num DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            events = []
            for r in rows:
                item = dict(r)
                if "event_id" in item and "evidence_id" not in item:
                    item["evidence_id"] = item["event_id"]
                if isinstance(item.get("findings"), str):
                    try:
                        item["findings"] = json.loads(item["findings"])
                    except Exception:
                        pass
                events.append(item)
            return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tamper")
def tamper_latest_event():
    """Adversarial tamper trigger: modifies stored decision in latest evidence record."""
    try:
        with sqlite3.connect(global_ledger.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT seq_num, decision FROM evidence ORDER BY seq_num DESC LIMIT 1")
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=400, detail="No ledger events to tamper.")
            seq_num, decision = row
            new_decision = "REJECT" if decision == "ACCEPT" else "ACCEPT"
            cursor.execute("UPDATE evidence SET decision = ? WHERE seq_num = ?", (new_decision, seq_num))
            conn.commit()
            return {"status": "TAMPERED", "seq_num": seq_num, "new_decision": new_decision}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
