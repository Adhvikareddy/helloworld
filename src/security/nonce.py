import threading
import time

class NonceGuard:
    """
    Validates that the nonce has not been used before (semantic freshness).
    """
    def __init__(self):
        self.seen_nonces = set()
        self.lock = threading.Lock()

    def is_fresh(self, nonce: str) -> bool:
        with self.lock:
            if nonce in self.seen_nonces:
                return False
            self.seen_nonces.add(nonce)
            return True

class TimestampGuard:
    """
    Validates that the request timestamp is fresh (request freshness).
    """
    @staticmethod
    def is_valid(timestamp: float, max_age_seconds: float = 300) -> bool:
        current = time.time()
        # allow small future drift due to clock sync issues
        if timestamp > current + 60: 
            return False
        if timestamp < current - max_age_seconds:
            return False
        return True
