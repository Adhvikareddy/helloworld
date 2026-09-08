"""
Integration tests for the Q-SENTINEL API using ASGITransport.
"""
import pytest
from fastapi.testclient import TestClient
import httpx
import time
import uuid

from apps.api.main import app
from src.security.envelope import PQCEnvelope
from src.keyvault import global_keyvault

# We can bypass external setup by injecting directly into the globals
# for testing purposes.

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def provisioned_keys():
    alice_pk, alice_sk = PQCEnvelope.generate_keypair()
    mallory_pk, mallory_sk = PQCEnvelope.generate_keypair()
    
    # Register Alice
    from src.security.identity import global_pqc_identity
    import base64
    global_pqc_identity.register_participant("alice", alice_pk, is_verifier=False)
    global_pqc_identity.register_participant("bob", alice_pk, is_verifier=True)
    global_pqc_identity.register_participant("mallory", mallory_pk, is_verifier=False)
    global_pqc_identity.register_participant("admin", alice_pk, is_verifier=True)
    
    # Provision a session for Alice in the keyvault
    session = global_keyvault.create_session("alice", 30)
    
    return {
        "alice_sk": alice_sk,
        "mallory_sk": mallory_sk,
        "session_id": session.session_id
    }

def test_legitimate_request(client, provisioned_keys):
    payload = {
        "session_id": provisioned_keys["session_id"],
        "signer_id": "alice",
        "verifier_id": "admin",
        "nonce": f"nonce-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": 0,
        "measurement_bases": ["X", "Y", "Z"] * 10,
        "experiment_id": None
    }
    
    sig = PQCEnvelope.sign_payload(provisioned_keys["alice_sk"], payload)
    payload["signature"] = sig
    
    response = client.post("/v1/qds/verify", json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["decision"] == "ACCEPT", response.text

def test_impersonation(client, provisioned_keys):
    # Second session because the first one is used up
    session = global_keyvault.create_session("alice", 30)
    
    payload = {
        "session_id": session.session_id,
        "signer_id": "alice",
        "verifier_id": "bob",
        "nonce": f"nonce-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": 0,
        "measurement_bases": ["X", "Y", "Z"] * 10,
        "experiment_id": None
    }
    
    # Signed by Mallory but claiming to be Alice
    sig = PQCEnvelope.sign_payload(provisioned_keys["mallory_sk"], payload)
    payload["signature"] = sig
    
    response = client.post("/v1/qds/verify", json=payload)
    assert response.status_code == 200
    assert response.json()["decision"] == "REJECT"

def test_replay_attack(client, provisioned_keys):
    session = global_keyvault.create_session("alice", 30)
    
    payload = {
        "session_id": session.session_id,
        "signer_id": "alice",
        "verifier_id": "bob",
        "nonce": f"fixed-nonce-123",
        "timestamp": time.time(),
        "message_bit": 0,
        "measurement_bases": ["X", "Y", "Z"] * 10,
        "experiment_id": None
    }
    
    sig = PQCEnvelope.sign_payload(provisioned_keys["alice_sk"], payload)
    payload["signature"] = sig
    
    # First request
    response1 = client.post("/v1/qds/verify", json=payload)
    assert response1.status_code == 200
    
    # We need a new session ID for the replay because the keyvault will block reuse
    # But wait, replay attacks use the SAME session ID!
    # The L3 freshness probe should catch it before the keyvault is hit.
    
    # Second request
    response2 = client.post("/v1/qds/verify", json=payload)
    assert response2.status_code == 200
    
    # Verify the finding shows replay (wait, side channel protection masks the finding to 'Gateway')
    findings = response2.json()["findings"]
    assert len(findings) == 1
    assert findings[0]["detector"] == "Gateway"
    assert response2.json()["decision"] == "REJECT"

