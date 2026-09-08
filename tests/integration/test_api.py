"""
Integration tests for the Q-SENTINEL v9.1 API (distribute, reveal, verify flow).
"""
import pytest
from fastapi.testclient import TestClient
import time
import uuid

from apps.api.main import app
from src.security.envelope import PQCEnvelope
from src.security.identity import global_pqc_identity
from src.keyvault.session_store import global_session_store

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def provisioned_keys():
    alice_pk, alice_sk = PQCEnvelope.generate_keypair()
    mallory_pk, mallory_sk = PQCEnvelope.generate_keypair()
    
    global_pqc_identity.register_participant("alice", alice_pk, is_verifier=False)
    global_pqc_identity.register_participant("bob", alice_pk, is_verifier=True)
    global_pqc_identity.register_participant("charlie", alice_pk, is_verifier=True)
    global_pqc_identity.register_participant("mallory", mallory_pk, is_verifier=False)
    
    return {
        "alice_sk": alice_sk,
        "mallory_sk": mallory_sk,
    }

def test_full_qds_v91_flow(client, provisioned_keys):
    session_id = f"test-session-{uuid.uuid4()}"
    
    # 1. Distribute phase
    dist_payload = {
        "session_id": session_id,
        "signer_id": "alice",
        "verifiers": ["bob", "charlie"],
        "L": 30,
        "nonce": f"nonce-dist-{uuid.uuid4()}",
        "timestamp": time.time(),
        "disturbance": 0.0
    }
    dist_sig = PQCEnvelope.sign_payload(provisioned_keys["alice_sk"], dist_payload)
    dist_payload["signature"] = dist_sig

    res_dist = client.post("/v1/qds/distribute", json=dist_payload)
    assert res_dist.status_code == 200, res_dist.text
    assert res_dist.json()["status"] == "DISTRIBUTED"

    # 2. Reveal phase
    rev_payload = {
        "session_id": session_id,
        "signer_id": "alice",
        "message_bit": 0,
        "nonce": f"nonce-rev-{uuid.uuid4()}",
        "timestamp": time.time()
    }
    rev_sig = PQCEnvelope.sign_payload(provisioned_keys["alice_sk"], rev_payload)
    rev_payload["signature"] = rev_sig

    res_rev = client.post("/v1/qds/reveal", json=rev_payload)
    assert res_rev.status_code == 200, res_rev.text
    revealed_keys = res_rev.json()["revealed_keys"]
    assert len(revealed_keys) == 30

    # 3. Verify phase (Bob)
    ver_payload = {
        "session_id": session_id,
        "signer_id": "alice",
        "verifier_id": "bob",
        "nonce": f"nonce-ver-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": 0,
        "revealed_keys": revealed_keys
    }
    ver_sig = PQCEnvelope.sign_payload(provisioned_keys["alice_sk"], ver_payload)
    ver_payload["signature"] = ver_sig

    res_ver = client.post("/v1/qds/verify", json=ver_payload)
    assert res_ver.status_code == 200, res_ver.text
    assert res_ver.json()["decision"] == "ACCEPT"

def test_impersonation_v91(client, provisioned_keys):
    session_id = f"test-session-{uuid.uuid4()}"
    
    dist_payload = {
        "session_id": session_id,
        "signer_id": "alice",
        "verifiers": ["bob"],
        "L": 30,
        "nonce": f"nonce-dist-{uuid.uuid4()}",
        "timestamp": time.time(),
        "disturbance": 0.0
    }
    dist_sig = PQCEnvelope.sign_payload(provisioned_keys["alice_sk"], dist_payload)
    dist_payload["signature"] = dist_sig
    client.post("/v1/qds/distribute", json=dist_payload)

    rev_payload = {
        "session_id": session_id,
        "signer_id": "alice",
        "message_bit": 0,
        "nonce": f"nonce-rev-{uuid.uuid4()}",
        "timestamp": time.time()
    }
    rev_sig = PQCEnvelope.sign_payload(provisioned_keys["alice_sk"], rev_payload)
    rev_payload["signature"] = rev_sig
    res_rev = client.post("/v1/qds/reveal", json=rev_payload)
    revealed_keys = res_rev.json()["revealed_keys"]

    ver_payload = {
        "session_id": session_id,
        "signer_id": "alice",
        "verifier_id": "bob",
        "nonce": f"nonce-ver-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": 0,
        "revealed_keys": revealed_keys
    }
    # Signed by Mallory but claiming Alice
    ver_sig = PQCEnvelope.sign_payload(provisioned_keys["mallory_sk"], ver_payload)
    ver_payload["signature"] = ver_sig

    res_ver = client.post("/v1/qds/verify", json=ver_payload)
    assert res_ver.status_code == 200
    assert res_ver.json()["decision"] == "REJECT"
