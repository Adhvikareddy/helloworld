"""
Integration tests for fail-closed security invariants (T5).

Tests:
11a. Corrupt thresholds.json -> the API returns 503, never ACCEPT.
11b. Missing thresholds file -> the API returns 503, never ACCEPT.
12a. StatisticalProbe raising an exception -> REJECT, never ACCEPT. Inject fault with monkeypatch.
12b. TomographyProbe raising an exception -> REJECT, never ACCEPT. Inject fault with monkeypatch.
"""
import pytest
from fastapi.testclient import TestClient
import time
import uuid
import os
import json

from apps.api.main import app
from src.security.envelope import PQCEnvelope
from src.security.identity import global_pqc_identity
from src.detection.policy import global_policy
from src.detection.probes import StatisticalProbe, TomographyProbe


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def failclosed_setup():
    alice_pk, alice_sk = PQCEnvelope.generate_keypair()
    global_pqc_identity.register_participant("alice_failclosed", alice_pk, is_verifier=False, role="verifier")
    global_pqc_identity.register_participant("bob_failclosed", alice_pk, is_verifier=True, role="verifier")
    
    return {
        "alice_sk": alice_sk,
        "signer_id": "alice_failclosed",
        "verifier_id": "bob_failclosed"
    }


def _create_and_reveal_session(client, setup, L=30):
    session_id = f"test-failclosed-{uuid.uuid4()}"
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


def test_corrupt_thresholds_returns_503_never_accept(client, failclosed_setup):
    """Test 11a: Corrupted thresholds.json causes verify endpoint to fail closed with 503."""
    session_id, legit_keys = _create_and_reveal_session(client, failclosed_setup)
    
    thresholds_file = global_policy.filepath
    backup_content = None
    if os.path.exists(thresholds_file):
        with open(thresholds_file, "r") as f:
            backup_content = f.read()

    try:
        # Write corrupted JSON
        with open(thresholds_file, "w") as f:
            f.write("{ INVALID JSON DATA 999 ### }")

        ver_payload = {
            "session_id": session_id,
            "signer_id": failclosed_setup["signer_id"],
            "verifier_id": failclosed_setup["verifier_id"],
            "nonce": f"nonce-ver-{uuid.uuid4()}",
            "timestamp": time.time(),
            "message_bit": 0,
            "revealed_keys": legit_keys
        }
        ver_payload["signature"] = PQCEnvelope.sign_payload(failclosed_setup["alice_sk"], ver_payload)
        
        res = client.post("/v1/qds/verify", json=ver_payload)
        assert res.status_code == 503
    finally:
        if backup_content is not None:
            with open(thresholds_file, "w") as f:
                f.write(backup_content)
        global_policy.load_thresholds()


def test_missing_thresholds_file_returns_503(client, failclosed_setup):
    """Test 11b: Missing thresholds file causes verify endpoint to fail closed with 503."""
    session_id, legit_keys = _create_and_reveal_session(client, failclosed_setup)

    thresholds_file = global_policy.filepath
    backup_content = None
    if os.path.exists(thresholds_file):
        with open(thresholds_file, "r") as f:
            backup_content = f.read()
        os.remove(thresholds_file)

    try:
        ver_payload = {
            "session_id": session_id,
            "signer_id": failclosed_setup["signer_id"],
            "verifier_id": failclosed_setup["verifier_id"],
            "nonce": f"nonce-ver-{uuid.uuid4()}",
            "timestamp": time.time(),
            "message_bit": 0,
            "revealed_keys": legit_keys
        }
        ver_payload["signature"] = PQCEnvelope.sign_payload(failclosed_setup["alice_sk"], ver_payload)

        res = client.post("/v1/qds/verify", json=ver_payload)
        assert res.status_code == 503
    finally:
        if backup_content is not None:
            with open(thresholds_file, "w") as f:
                f.write(backup_content)
        global_policy.load_thresholds()


def test_statistical_probe_exception_fails_closed_to_reject_never_accept(client, failclosed_setup, monkeypatch):
    """Test 12a: Exception in StatisticalProbe produces REJECT finding, never ACCEPT."""
    session_id, legit_keys = _create_and_reveal_session(client, failclosed_setup)

    def faulty_evaluate(*args, **kwargs):
        raise RuntimeError("Simulated statistical detector crash")

    monkeypatch.setattr(StatisticalProbe, "evaluate", faulty_evaluate)

    ver_payload = {
        "session_id": session_id,
        "signer_id": failclosed_setup["signer_id"],
        "verifier_id": failclosed_setup["verifier_id"],
        "nonce": f"nonce-ver-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": 0,
        "revealed_keys": legit_keys
    }
    ver_payload["signature"] = PQCEnvelope.sign_payload(failclosed_setup["alice_sk"], ver_payload)

    res = client.post("/v1/qds/verify", json=ver_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "REJECT", f"Expected REJECT on probe fault, got {data['decision']}"


def test_tomography_probe_exception_fails_closed_to_reject(client, failclosed_setup, monkeypatch):
    """Test 12b: Exception in TomographyProbe produces REJECT finding, never ACCEPT."""
    session_id, legit_keys = _create_and_reveal_session(client, failclosed_setup)

    def faulty_tomography(*args, **kwargs):
        raise RuntimeError("Simulated tomography probe crash")

    monkeypatch.setattr(TomographyProbe, "evaluate", faulty_tomography)

    ver_payload = {
        "session_id": session_id,
        "signer_id": failclosed_setup["signer_id"],
        "verifier_id": failclosed_setup["verifier_id"],
        "nonce": f"nonce-ver-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": 0,
        "revealed_keys": legit_keys
    }
    ver_payload["signature"] = PQCEnvelope.sign_payload(failclosed_setup["alice_sk"], ver_payload)

    res = client.post("/v1/qds/verify", json=ver_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "REJECT", f"Expected REJECT on probe fault, got {data['decision']}"
