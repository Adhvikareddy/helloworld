"""
Timing Oracle Attack Scenario.

Tests if the API is vulnerable to timing side channels by sending
requests that fail early (e.g., bad signature) vs late (e.g., bad quantum).
"""
import time
from src.transport.client import TransportClient

def run_timing_oracle(client: TransportClient, valid_payload: dict, invalid_auth_payload: dict):
    print("Running timing oracle check...")
    
    # Warm up connection so TCP/TLS handshake is not measured as API verification latency
    try:
        client.client.get("/v1/health")
    except Exception:
        pass

    # 1. Measure invalid auth (should fail at L3)
    t0 = time.time()
    try:
        client.post_verification(invalid_auth_payload)
    except Exception:
        pass
    t_invalid = time.time() - t0
    
    # 2. Measure valid auth (proceeds to L1/L2)
    t0 = time.time()
    try:
        client.post_verification(valid_payload)
    except Exception:
        pass
    t_valid = time.time() - t0
    
    diff = abs(t_valid - t_invalid)
    print(f"Time Invalid Auth: {t_invalid:.3f}s")
    print(f"Time Valid Auth:   {t_valid:.3f}s")
    print(f"Delta:             {diff:.3f}s")
    
    if diff > 0.5:
        print("VULNERABLE: Timing side channel detected.")
        return False
    else:
        print("SECURE: Constant-time envelope is effective.")
        return True

