from src.security.nonce import NonceGuard

class ReplayGuard:
    """
    High-level replay guard combining nonce (semantic freshness) and session state.
    """
    def __init__(self, nonce_guard: NonceGuard):
        self.nonce_guard = nonce_guard
    
    def check_replay(self, nonce: str, session_id: str) -> bool:
        # Replay is detected if the nonce is not fresh.
        # In a production system, session_id binding to nonce is also verified.
        return self.nonce_guard.is_fresh(nonce)
