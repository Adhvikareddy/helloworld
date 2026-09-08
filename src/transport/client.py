"""
Q-SENTINEL Transport Client.

Abstracts the physical transport layer for the verification API.
Supports httpx for integration testing (Track A) and HTTP over
a segmented Docker network (Track B).
"""
import httpx
from typing import Dict, Any, Optional

class TransportClient:
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(base_url=self.base_url, timeout=10.0)
        
    def post_verification(self, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        """Send a verification request to the API."""
        return self.client.post("/v1/qds/verify", json=payload, headers=headers)
        
    def close(self):
        self.client.close()

