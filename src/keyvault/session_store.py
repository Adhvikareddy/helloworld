"""
SQLite-backed Session Store for Q-SENTINEL Key Vault & Distribution.

Implements persistent storage for pre-distributed quantum keys, verifier bit states,
and double-consumption prevention.
"""
import sqlite3
import os
import json
from typing import Dict, List, Optional, Tuple, Any

class SessionStore:
    def __init__(self, db_path: str = "qsentinel_sessions.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS distribution_records (
                session_id TEXT PRIMARY KEY,
                signer_id TEXT NOT NULL,
                L INTEGER NOT NULL,
                created_at REAL NOT NULL
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS distribution_sessions (
                session_id TEXT NOT NULL,
                verifier_id TEXT NOT NULL,
                bit_index INTEGER NOT NULL,
                base TEXT NOT NULL,
                outcome INTEGER NOT NULL,
                PRIMARY KEY (session_id, verifier_id, bit_index)
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS verification_consumed (
                session_id TEXT NOT NULL,
                verifier_id TEXT NOT NULL,
                consumed_at REAL NOT NULL,
                PRIMARY KEY (session_id, verifier_id)
            );
            """)
            conn.commit()

    def create_session_record(self, session_id: str, signer_id: str, L: int, created_at: float):
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO distribution_records (session_id, signer_id, L, created_at) VALUES (?, ?, ?, ?)",
                (session_id, signer_id, L, created_at)
            )
            conn.commit()

    def store_verifier_outcomes(self, session_id: str, verifier_id: str, bases: List[str], outcomes: List[int]):
        with self._get_connection() as conn:
            data = [
                (session_id, verifier_id, idx, b, o)
                for idx, (b, o) in enumerate(zip(bases, outcomes))
            ]
            conn.executemany(
                "INSERT INTO distribution_sessions (session_id, verifier_id, bit_index, base, outcome) VALUES (?, ?, ?, ?, ?)",
                data
            )
            conn.commit()

    def get_session_record(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT session_id, signer_id, L, created_at FROM distribution_records WHERE session_id = ?",
                (session_id,)
            ).fetchone()
            if row:
                return dict(row)
            return None

    def get_verifier_outcomes(self, session_id: str, verifier_id: str) -> Optional[Tuple[List[str], List[int]]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT base, outcome FROM distribution_sessions WHERE session_id = ? AND verifier_id = ? ORDER BY bit_index ASC",
                (session_id, verifier_id)
            ).fetchall()
            if not rows:
                return None
            bases = [r["base"] for r in rows]
            outcomes = [r["outcome"] for r in rows]
            return bases, outcomes

    def is_consumed(self, session_id: str, verifier_id: str) -> bool:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM verification_consumed WHERE session_id = ? AND verifier_id = ?",
                (session_id, verifier_id)
            ).fetchone()
            return row is not None

    def mark_consumed(self, session_id: str, verifier_id: str, timestamp: float) -> bool:
        with self._get_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO verification_consumed (session_id, verifier_id, consumed_at) VALUES (?, ?, ?)",
                    (session_id, verifier_id, timestamp)
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def clear(self):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM distribution_records")
            conn.execute("DELETE FROM distribution_sessions")
            conn.execute("DELETE FROM verification_consumed")
            conn.commit()

global_session_store = SessionStore()
