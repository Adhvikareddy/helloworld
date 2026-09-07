import sqlite3
import hashlib
import json
import os

class EvidenceLedger:
    """
    Append-only local hash-chain for Q-SENTINEL.
    """
    def __init__(self, db_path="data/ledger.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE,
                timestamp TEXT,
                session_id TEXT,
                signer_id TEXT,
                verifier_id TEXT,
                decision TEXT,
                reason TEXT,
                deviation_score REAL,
                chi_square REAL,
                threshold_low REAL,
                threshold_high REAL,
                baseline_version TEXT,
                detector_version TEXT,
                experiment_id TEXT,
                previous_hash TEXT,
                current_hash TEXT
            )
        ''')
        self.conn.commit()

    def _get_last_hash(self) -> str:
        self.cursor.execute("SELECT current_hash FROM evidence ORDER BY id DESC LIMIT 1")
        row = self.cursor.fetchone()
        return row[0] if row else "0000000000000000000000000000000000000000000000000000000000000000"

    def record_event(self, event_data: dict) -> str:
        previous_hash = self._get_last_hash()
        
        # Canonicalize event
        # Only include specific fields to avoid hash mismatch issues on verification
        canonical_fields = {
            k: v for k, v in event_data.items() 
            if k not in ['previous_hash', 'current_hash'] and v is not None
        }
        
        canonical_event = json.dumps(canonical_fields, sort_keys=True)
        current_hash = hashlib.sha256((previous_hash + canonical_event).encode('utf-8')).hexdigest()
        
        self.cursor.execute('''
            INSERT INTO evidence (
                event_id, timestamp, session_id, signer_id, verifier_id, decision,
                reason, deviation_score, chi_square, threshold_low, threshold_high,
                baseline_version, detector_version, experiment_id, previous_hash, current_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event_data.get('event_id'), event_data.get('timestamp'), event_data.get('session_id'),
            event_data.get('signer_id'), event_data.get('verifier_id'), event_data.get('decision'),
            event_data.get('reason'), event_data.get('deviation_score'), event_data.get('chi_square'),
            event_data.get('threshold_low'), event_data.get('threshold_high'),
            event_data.get('baseline_version'), event_data.get('detector_version'),
            event_data.get('experiment_id'), previous_hash, current_hash
        ))
        self.conn.commit()
        return current_hash

    def get_event(self, event_id: str) -> dict:
        self.cursor.execute("SELECT * FROM evidence WHERE event_id=?", (event_id,))
        row = self.cursor.fetchone()
        if not row:
            return None
        cols = [description[0] for description in self.cursor.description]
        return dict(zip(cols, row))
