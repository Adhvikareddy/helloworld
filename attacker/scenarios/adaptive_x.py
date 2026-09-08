"""
Q-SENTINEL Adaptive X-Rotation Regression.

Tests whether the system detects pure X-axis rotations (F3 evasion path).
"""
import time
from src.transport.client import TransportClient

def run_adaptive_x_test(client: TransportClient, valid_payload: dict = None):
    print("Running adaptive X-rotation test (F3 regression)...")
    from attacker.client import get_base_payload
    payload = get_base_payload(disturbance=0.5)
    headers = {"Content-Type": "application/json", "x-role": "auditor"}
    resp = client.post_verification(payload, headers=headers)
    
    if resp.status_code != 200:
        print("API Error:", resp.text)
        return False
        
    data = resp.json()
    
    # If the system correctly detects disturbance, it should REJECT or QUARANTINE it.
    if data.get("decision") == "ACCEPT":
        print("VULNERABLE: Channel disturbance was ACCEPTED. F3 is present.")
        return False
    else:
        print(f"SECURE: Channel disturbance detected and handled ({data.get('decision')}).")
        return True
