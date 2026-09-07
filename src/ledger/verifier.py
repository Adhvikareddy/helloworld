import hashlib
import json
from src.ledger.hash_chain import EvidenceLedger

class LedgerVerifier:
    """
    Verifies the hash chain integrity of the ledger.
    """
    def __init__(self, ledger: EvidenceLedger):
        self.ledger = ledger

    def verify_chain(self) -> dict:
        self.ledger.cursor.execute("SELECT * FROM evidence ORDER BY id ASC")
        rows = self.ledger.cursor.fetchall()
        cols = [desc[0] for desc in self.ledger.cursor.description]
        
        previous_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        
        for row in rows:
            record = dict(zip(cols, row))
            
            # Reconstruct the canonical dict that was hashed
            canonical_fields = {
                k: v for k, v in record.items() 
                if k not in ['id', 'previous_hash', 'current_hash'] and v is not None
            }
            
            canonical_event = json.dumps(canonical_fields, sort_keys=True)
            expected_hash = hashlib.sha256((previous_hash + canonical_event).encode('utf-8')).hexdigest()
            
            if record["previous_hash"] != previous_hash:
                return {"valid": False, "reason": f"Broken chain at event {record['event_id']}: invalid previous_hash"}
                
            if record["current_hash"] != expected_hash:
                return {"valid": False, "reason": f"Integrity violation at event {record['event_id']}: invalid current_hash"}
                
            previous_hash = record["current_hash"]
            
        return {"valid": True, "reason": "Chain is intact", "records_verified": len(rows)}
