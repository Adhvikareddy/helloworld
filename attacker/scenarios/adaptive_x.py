"""
Q-SENTINEL Adaptive X-Rotation Regression.

Tests whether the system detects pure X-axis rotations (F3 evasion path).
"""
import time
from src.transport.client import TransportClient

def run_adaptive_x_test(client: TransportClient, valid_payload: dict):
    print("Running adaptive X-rotation test (F3 regression)...")
    
    # Send a request with a specific testbed header that instructs the simulator
    # to apply pure X rotations instead of the default rx+rz depolarizing noise.
    # The API will pass this to the QDS core if the experiment_id triggers it.
    
    payload = valid_payload.copy()
    payload["experiment_id"] = "test_pure_x_rotation"
    
    headers = {"x-testbed-disturbance": "0.5"}
    
    resp = client.post_verification(payload, headers=headers)
    
    if resp.status_code != 200:
        print("API Error:", resp.text)
        return False
        
    data = resp.json()
    
    # If the system correctly randomizes states (not just |+>), it should detect the X-rotation
    # as a disturbance and REJECT or QUARANTINE it.
    if data["decision"] == "ACCEPT":
        print("VULNERABLE: Pure X-rotation was ACCEPTED. F3 is present.")
        return False
    else:
        print(f"SECURE: Pure X-rotation detected and handled ({data['decision']}).")
        return True
