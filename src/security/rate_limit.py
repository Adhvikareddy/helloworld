"""
Q-SENTINEL Rate Limiter.

Basic sliding window rate limiting.
"""
import time
from collections import deque
from fastapi import HTTPException
import threading

class RateLimiter:
    def __init__(self, requests: int = 1000, window_seconds: int = 60):
        self.requests = requests
        self.window = window_seconds
        self.history = {}
        self.lock = threading.Lock()

    def check_rate_limit(self, client_id: str):
        now = time.time()
        with self.lock:
            if client_id not in self.history:
                self.history[client_id] = deque()
                
            q = self.history[client_id]
            
            # Remove old entries
            while q and q[0] < now - self.window:
                q.popleft()
                
            if len(q) >= self.requests:
                raise HTTPException(status_code=429, detail="Too Many Requests")
                
            q.append(now)

# Global instance for the API
global_rate_limiter = RateLimiter(requests=1000, window_seconds=60)
