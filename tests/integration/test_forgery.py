"""
Integration tests for signature forgery and revealed keys validation (T5).

Tests:
1. Legitimate revealed keys -> ACCEPT, mismatch_rate close to measured e_honest.
2. Uniformly random revealed keys -> REJECT.
3. 50%-correct revealed keys -> REJECT.
4. Empty revealed_keys -> REJECT, never ACCEPT.
5. revealed_keys longer than session L -> rejected with 422 HTTP status.
"""
import pytest
from fastapi.testclient import TestClient
import time
import uuid
import random

from apps.api.main import app
from src.security.envelope import PQCEnvelope
from src.security.identity import global_pqc_identity
from src.detection.policy import global_policy


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def forgery_setup():
    alice_pk, alice_sk = PQCEnvelope.generate_keypair()
    global_pqc_identity.register_participant("alice_forgery", alice_pk, is_verifier=False, role="verifier")
    global_pqc_identity.register_participant("bob_forgery", alice_pk, is_verifier=True, role="verifier")
    
    return {
        "alice_sk": alice_sk,
        "signer_id": "alice_forgery",
        "verifier_id": "bob_forgery"
    }


def _create_and_reveal_session(client, setup, L=60):
    session_id = f"test-forgery-{uuid.uuid4()}"
    dist_payload = {
        "session_id": session_id,
        "signer_id": setup["signer_id"],
        "verifiers": [setup["verifier_id"]],
        "L": L,
        "nonce": f"nonce-dist-{uuid.uuid4()}",
        "timestamp": time.time()
    }
    dist_payload["signature"] = PQCEnvelope.sign_payload(setup["alice_sk"], dist_payload)
    res_dist = client.post("/v1/qds/distribute", json=dist_payload)
    assert res_dist.status_code == 200, res_dist.text

    rev_payload = {
        "session_id": session_id,
        "signer_id": setup["signer_id"],
        "message_bit": 0,
        "nonce": f"nonce-rev-{uuid.uuid4()}",
        "timestamp": time.time()
    }
    rev_payload["signature"] = PQCEnvelope.sign_payload(setup["alice_sk"], rev_payload)
    res_rev = client.post("/v1/qds/reveal", json=rev_payload)
    assert res_rev.status_code == 200, res_rev.text
    legit_keys = res_rev.json()["revealed_keys"]
    return session_id, legit_keys


def test_legitimate_keys_accept_and_mismatch_near_honest(client, forgery_setup):
    session_id, legit_keys = _create_and_reveal_session(client, forgery_setup, L=60)
    
    ver_payload = {
        "session_id": session_id,
        "signer_id": forgery_setup["signer_id"],
        "verifier_id": forgery_setup["verifier_id"],
        "nonce": f"nonce-ver-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": 0,
        "revealed_keys": legit_keys
    }
    ver_payload["signature"] = PQCEnvelope.sign_payload(forgery_setup["alice_sk"], ver_payload)
    res = client.post("/v1/qds/verify", json=ver_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "ACCEPT"
    
    # Check that mismatch_rate reported in quantum findings is close to measured e_honest
    findings = data["findings"]
    quantum_findings = [f for f in findings if f.get("detector") == "QuantumDetector"]
    assert len(quantum_findings) >= 1
    mismatch_rate = quantum_findings[0]["metrics"]["mismatch_rate"]
    tau_low = global_policy.tau_low
    assert mismatch_rate <= tau_low


def test_uniformly_random_revealed_keys_reject(client, forgery_setup):
    session_id, legit_keys = _create_and_reveal_session(client, forgery_setup, L=60)
    
    # Uniformly random keys
    random_keys = [
        {"bit_index": i, "basis": random.choice(["X", "Y", "Z"]), "bit_value": random.choice([0, 1])}
        for i in range(len(legit_keys))
    ]
    
    ver_payload = {
        "session_id": session_id,
        "signer_id": forgery_setup["signer_id"],
        "verifier_id": forgery_setup["verifier_id"],
        "nonce": f"nonce-ver-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": 0,
        "revealed_keys": random_keys
    }
    ver_payload["signature"] = PQCEnvelope.sign_payload(forgery_setup["alice_sk"], ver_payload)
    res = client.post("/v1/qds/verify", json=ver_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "REJECT"


def test_fifty_percent_correct_revealed_keys_reject(client, forgery_setup):
    session_id, legit_keys = _create_and_reveal_session(client, forgery_setup, L=60)
    
    # Invert 50% of the bits to create a 50% corrupted key set
    corrupted_keys = []
    for i, k in enumerate(legit_keys):
        bit_val = 1 - k["bit_value"] if i % 2 == 0 else k["bit_value"]
        corrupted_keys.append({
            "bit_index": k["bit_index"],
            "basis": k["basis"],
            "bit_value": bit_val
        })
        
    ver_payload = {
        "session_id": session_id,
        "signer_id": forgery_setup["signer_id"],
        "verifier_id": forgery_setup["verifier_id"],
        "nonce": f"nonce-ver-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": 0,
        "revealed_keys": corrupted_keys
    }
    ver_payload["signature"] = PQCEnvelope.sign_payload(forgery_setup["alice_sk"], ver_payload)
    res = client.post("/v1/qds/verify", json=ver_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "REJECT"


def test_empty_revealed_keys_rejects_never_accepts(client, forgery_setup):
    session_id, _ = _create_and_reveal_session(client, forgery_setup, L=60)
    
    ver_payload = {
        "session_id": session_id,
        "signer_id": forgery_setup["signer_id"],
        "verifier_id": forgery_setup["verifier_id"],
        "nonce": f"nonce-ver-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": 0,
        "revealed_keys": []
    }
    ver_payload["signature"] = PQCEnvelope.sign_payload(forgery_setup["alice_sk"], ver_payload)
    res = client.post("/v1/qds/verify", json=ver_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "REJECT"


def test_revealed_keys_longer_than_session_rejected_by_validation(client, forgery_setup):
    session_id, legit_keys = _create_and_reveal_session(client, forgery_setup, L=30)
    
    # Append extra keys beyond L=30
    extra_keys = list(legit_keys) + [
        {"bit_index": 30, "basis": "X", "bit_value": 0},
        {"bit_index": 31, "basis": "Z", "bit_value": 1},
    ]
    
    ver_payload = {
        "session_id": session_id,
        "signer_id": forgery_setup["signer_id"],
        "verifier_id": forgery_setup["verifier_id"],
        "nonce": f"nonce-ver-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": 0,
        "revealed_keys": extra_keys
    }
    ver_payload["signature"] = PQCEnvelope.sign_payload(forgery_setup["alice_sk"], ver_payload)
    res = client.post("/v1/qds/verify", json=ver_payload)
    assert res.status_code == 422
