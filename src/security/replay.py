"""
Q-SENTINEL Replay Guard.

High-level replay guard combining SQLite-backed nonce tracking and session state.
"""
from src.security.nonce import SQLiteNonceGuard


class ReplayGuard:
    """
    High-level replay guard combining nonce (semantic freshness) and session state.
    """
    def __init__(self, nonce_guard: SQLiteNonceGuard):
        self.nonce_guard = nonce_guard
    
    def check_replay(self, nonce: str, session_id: str) -> bool:
        # Replay is detected if the nonce is not fresh.
        # In a production system, session_id binding to nonce is also verified.
        return self.nonce_guard.is_fresh(nonce, session_id)
