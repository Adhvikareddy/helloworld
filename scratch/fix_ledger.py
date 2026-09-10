import sys
sys.path.insert(0, ".")
import sqlite3
import hashlib
import json
from src.ledger.hash_chain import global_ledger
from src.ledger.verifier import verify_ledger

db_path = global_ledger.db_path

with sqlite3.connect(db_path) as conn:
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM evidence ORDER BY seq_num ASC")
    rows = [dict(r) for r in c.fetchall()]

print(f"Total rows: {len(rows)}")

fixed_count = 0
for i in range(1, len(rows)):
    row = rows[i]
    prev = rows[i - 1]['current_hash']
    
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
    h = hashlib.sha256(prev.encode('utf-8') + canonical_event).hexdigest()
    
    if h != row['current_hash']:
        # Try alternate decisions
        for alt in ["ACCEPT", "REJECT", "QUARANTINE", "DISTRIBUTED", "INFO"]:
            if alt == row['decision']:
                continue
            canonical_fields['decision'] = alt
            alt_event = json.dumps(canonical_fields, sort_keys=True).encode('utf-8')
            alt_h = hashlib.sha256(prev.encode('utf-8') + alt_event).hexdigest()
            if alt_h == row['current_hash']:
                print(f"Fixed row {row['seq_num']}: '{row['decision']}' -> '{alt}'")
                with sqlite3.connect(db_path) as fix_conn:
                    fix_conn.execute("UPDATE evidence SET decision = ? WHERE seq_num = ?", (alt, row['seq_num']))
                row['decision'] = alt
                fixed_count += 1
                break

print(f"Fixed {fixed_count} rows.")
print("Ledger verification result:", verify_ledger(db_path))
