"""
Q-SENTINEL Attack Execution Script.

Runs all the attack scenarios against the live API.
"""
import httpx
import time
import json
from src.transport.client import TransportClient
from attacker.harness import AttackerHarness
from attacker.scenarios.timing_oracle import run_timing_oracle
from attacker.scenarios.adaptive_x import run_adaptive_x_test


def run_all_attacks():
    client = TransportClient("http://localhost:8000")
    harness = AttackerHarness()
    
    # Needs a valid session from the keyvault to pass L1 properly
    # In a real run, this would be requested via a setup endpoint.
    # For now, we'll manually pre-provision one in the vault for testing.
    import requests
    # Wait for API to be up
    for _ in range(5):
        try:
            requests.get("http://localhost:8000/v1/health")
            break
        except:
            time.sleep(1)
            
    print("\n--- Running Q-SENTINEL Adversarial Harness ---")
    
    # Generate a valid payload base
    valid_payload, _ = harness.replay_attack()
    # Replace session ID with one we know is in the vault (we'll inject it via a test endpoint or mock)
    
    # 1. Timing Oracle Test
    invalid_payload = harness.impersonate_alice()
    run_timing_oracle(client, valid_payload, invalid_payload)
    
    # 2. Adaptive X-Rotation
    run_adaptive_x_test(client, valid_payload)
    
    # The rest of the attacks will be run via Pytest integration tests to ensure
    # we can mock the KeyVault state correctly.

if __name__ == "__main__":
    run_all_attacks()
