"""
Integration tests for role-based response tiering (T2).

Verifies that:
1. An unprivileged caller attempting privilege escalation via 'x-role: admin'
   header receives redacted findings on REJECT.
2. An authenticated participant with registered role 'auditor' receives full metrics on REJECT.
"""
import pytest
from fastapi.testclient import TestClient
import time
import uuid

from apps.api.main import app
from src.security.envelope import PQCEnvelope
from src.security.identity import global_pqc_identity


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def tiering_setup():
    alice_pk, alice_sk = PQCEnvelope.generate_keypair()
    auditor_pk, auditor_sk = PQCEnvelope.generate_keypair()
    
    # Alice is standard verifier role
    global_pqc_identity.register_participant("alice", alice_pk, is_verifier=False, role="verifier")
    global_pqc_identity.register_participant("bob", alice_pk, is_verifier=True, role="verifier")
    # Auditor identity has role "auditor"
    global_pqc_identity.register_participant("auditor_party", auditor_pk, is_verifier=True, role="auditor")
    
    return {
        "alice_sk": alice_sk,
        "auditor_sk": auditor_sk,
    }


def _create_distribution_session(client, alice_sk, signer_id="alice"):
    session_id = f"test-tiering-{uuid.uuid4()}"
    dist_payload = {
        "session_id": session_id,
        "signer_id": signer_id,
        "verifiers": ["bob"],
        "L": 30,
        "nonce": f"nonce-dist-{uuid.uuid4()}",
        "timestamp": time.time()
    }
    dist_payload["signature"] = PQCEnvelope.sign_payload(alice_sk, dist_payload)
    res_dist = client.post("/v1/qds/distribute", json=dist_payload)
    assert res_dist.status_code == 200, res_dist.text
    return session_id


def test_unprivileged_caller_with_admin_header_gets_redacted(client, tiering_setup):
    session_id = _create_distribution_session(client, tiering_setup["alice_sk"], "alice")
    
    # Send forged revealed keys (e.g. all 1s with basis Z) to guarantee REJECT
    forged_keys = [{"bit_index": i, "basis": "Z", "bit_value": 1} for i in range(30)]
    ver_payload = {
        "session_id": session_id,
        "signer_id": "alice",
        "verifier_id": "bob",
        "nonce": f"nonce-ver-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": 0,
        "revealed_keys": forged_keys
    }
    ver_payload["signature"] = PQCEnvelope.sign_payload(tiering_setup["alice_sk"], ver_payload)
    
    # Attacker attempts privilege escalation via header
    headers = {"x-role": "admin"}
    res = client.post("/v1/qds/verify", json=ver_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "REJECT"
    findings = data["findings"]
    assert len(findings) == 1
    assert findings[0]["metrics"].get("findings_redacted") is True
    assert findings[0]["metrics"].get("tier") == "standard_verifier"


def test_authenticated_auditor_receives_full_metrics(client, tiering_setup):
    # Auditor distributes the session as signer
    session_id = _create_distribution_session(client, tiering_setup["auditor_sk"], "auditor_party")
    
    # Send forged revealed keys to guarantee REJECT
    forged_keys = [{"bit_index": i, "basis": "Z", "bit_value": 1} for i in range(30)]
    ver_payload = {
        "session_id": session_id,
        "signer_id": "auditor_party",
        "verifier_id": "bob",
        "nonce": f"nonce-ver-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": 0,
        "revealed_keys": forged_keys
    }
    ver_payload["signature"] = PQCEnvelope.sign_payload(tiering_setup["auditor_sk"], ver_payload)
    
    res = client.post("/v1/qds/verify", json=ver_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "REJECT"
    findings = data["findings"]
    # Auditor must receive full unredacted findings containing detector metrics
    assert not any(f.get("metrics", {}).get("findings_redacted") is True for f in findings)
    detector_names = [f.get("detector") for f in findings]
    assert "QuantumDetector" in detector_names
