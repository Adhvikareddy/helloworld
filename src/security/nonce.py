"""
Q-SENTINEL Nonce Guard.

Persisted nonce tracking to prevent replay attacks across worker restarts.
Uses SQLite to store seen nonces and their timestamps.
"""
import sqlite3
import time
import os

class SQLiteNonceGuard:
    def __init__(self, db_path: str = "data/nonces.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS seen_nonces (
                    nonce TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            ''')
            # Index for fast cleanup of old nonces
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON seen_nonces(timestamp)')
            conn.commit()

    def is_fresh(self, nonce: str, session_id: str) -> bool:
        """
        Check if a nonce is fresh (not seen before).
        Records the nonce if it is fresh.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Attempt to insert. If it exists, IntegrityError is raised.
                conn.execute(
                    'INSERT INTO seen_nonces (nonce, session_id, timestamp) VALUES (?, ?, ?)',
                    (nonce, session_id, time.time())
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def cleanup_old_nonces(self, max_age_seconds: float = 3600):
        """Remove nonces older than the max age."""
        cutoff = time.time() - max_age_seconds
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM seen_nonces WHERE timestamp < ?', (cutoff,))
            conn.commit()

class TimestampGuard:
    """Verify timestamp freshness to bound the size of the nonce store."""
    
    @staticmethod
    def is_valid(req_timestamp: float, max_age_seconds: float = 60) -> bool:
        """
        Check if timestamp is within the acceptable window.
        Allows for slight future drift (e.g. clock sync issues).
        """
        now = time.time()
        # Accept up to 60 seconds in the future, and max_age_seconds in the past
        return (now - max_age_seconds) <= req_timestamp <= (now + 60)

# Global instance
global_nonce_guard = SQLiteNonceGuard()
