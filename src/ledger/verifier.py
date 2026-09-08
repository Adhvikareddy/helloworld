"""
Q-SENTINEL Ledger Verifier.

Audits the ledger for tampering, verifying both the hash chain and the HMAC signatures.
"""
import sqlite3
import hmac
import hashlib
import json
from src.ledger.hash_chain import LEDGER_SECRET

def verify_ledger(db_path: str = "data/ledger.db") -> bool:
    """
    Verify the integrity of the entire ledger.
    Returns True if valid, False if tampered.
    """
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM evidence ORDER BY seq_num ASC")
        rows = cursor.fetchall()
        
        if not rows:
            return True # Empty ledger is valid
            
        # Check Genesis
        genesis = rows[0]
        if genesis['event_id'] != 'genesis':
            print("Genesis block tampered.")
            return False
            
        expected_sig = hmac.new(LEDGER_SECRET, genesis['current_hash'].encode('utf-8'), hashlib.sha256).hexdigest()
        if genesis['signature'] != expected_sig:
            print("Genesis signature invalid.")
            return False
            
        previous_hash = genesis['current_hash']
        
        for i in range(1, len(rows)):
            row = rows[i]
            
            # 1. Verify continuous linkage
            if row['previous_hash'] != previous_hash:
                print(f"Chain broken at seq_num {row['seq_num']}: previous_hash mismatch.")
                return False
                
            # 2. Verify Canonical Event Hash
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
                print(f"Hash mismatch at seq_num {row['seq_num']}. Data tampered.")
                return False
                
            # 3. Verify HMAC signature (Proof of Authorship)
            expected_sig = hmac.new(LEDGER_SECRET, row['current_hash'].encode('utf-8'), hashlib.sha256).hexdigest()
            if row['signature'] != expected_sig:
                print(f"Signature mismatch at seq_num {row['seq_num']}. Forge attempt detected.")
                return False
                
            previous_hash = row['current_hash']
            
        return True
