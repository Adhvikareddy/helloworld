"""
Integration tests for multi-vector threat detection and correlation (T5).

Tests:
13. A request combining 4 vectors returns 4 or more findings, and the response
    enumerates all of them.
"""
import pytest
from fastapi.testclient import TestClient
import time
import uuid

from apps.api.main import app
from src.security.envelope import PQCEnvelope
from src.security.identity import global_pqc_identity
from src.security.nonce import global_nonce_guard
from src.keyvault.session_store import global_session_store


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def multivector_setup():
    auditor_pk, auditor_sk = PQCEnvelope.generate_keypair()
    # Register as auditor so response tiering returns all unredacted diagnostic findings
    global_pqc_identity.register_participant("auditor_alice", auditor_pk, is_verifier=False, role="auditor")
    global_pqc_identity.register_participant("bob_mv", auditor_pk, is_verifier=True, role="verifier")
    
    return {
        "auditor_sk": auditor_sk,
        "signer_id": "auditor_alice",
        "verifier_id": "bob_mv"
    }


def test_multivector_request_returns_at_least_four_enumerated_findings(client, multivector_setup):
    session_id = f"test-multivector-{uuid.uuid4()}"
    L = 30
    
    # 1. Distribute valid session
    dist_payload = {
        "session_id": session_id,
        "signer_id": multivector_setup["signer_id"],
        "verifiers": [multivector_setup["verifier_id"]],
        "L": L,
        "nonce": f"nonce-dist-{uuid.uuid4()}",
        "timestamp": time.time()
    }
    dist_payload["signature"] = PQCEnvelope.sign_payload(multivector_setup["auditor_sk"], dist_payload)
    res_dist = client.post("/v1/qds/distribute", json=dist_payload)
    assert res_dist.status_code == 200

    # Vector 1: Replayed nonce (pre-register nonce in guard)
    replayed_nonce = f"nonce-replayed-{uuid.uuid4()}"
    assert global_nonce_guard.is_fresh(replayed_nonce, session_id) is True

    # Vector 2: Already consumed session (pre-mark consumed for this verifier)
    global_session_store.mark_consumed(session_id, multivector_setup["verifier_id"], time.time())

    # Vector 3: Stale timestamp (1 hour in the past)
    stale_timestamp = time.time() - 3600.0

    # Vector 4: Forged revealed keys (inverted / bad keys)
    forged_keys = [
        {"bit_index": i, "basis": "Z", "bit_value": 1}
        for i in range(L)
    ]

    ver_payload = {
        "session_id": session_id,
        "signer_id": multivector_setup["signer_id"],
        "verifier_id": multivector_setup["verifier_id"],
        "nonce": replayed_nonce,
        "timestamp": stale_timestamp,
        "message_bit": 0,
        "revealed_keys": forged_keys
    }
    ver_payload["signature"] = PQCEnvelope.sign_payload(multivector_setup["auditor_sk"], ver_payload)

    res = client.post("/v1/qds/verify", json=ver_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "REJECT"

    findings = data["findings"]
    assert len(findings) >= 4, f"Expected at least 4 findings, got {len(findings)}: {findings}"

    # Verify that distinct threat detectors are enumerated in the findings
    detectors = [f.get("detector") for f in findings]
    assert "TimestampGuard" in detectors, "TimestampGuard finding missing"
    assert "ReplayGuard" in detectors, "ReplayGuard finding missing"
    assert "DoubleConsumptionGuard" in detectors, "DoubleConsumptionGuard finding missing"
    assert "QuantumDetector" in detectors, "QuantumDetector finding missing"
