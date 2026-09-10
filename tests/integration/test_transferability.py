"""
Integration tests for QDS Transferability (T5).

Tests:
6. Bob fabricates from his own records -> Bob ACCEPTS.
   (Documented as expected behavior: Bob knows his own measurement basis and outcome
   at every position, giving zero mismatch against his own database).
7. The exact same fabrication submitted to Charlie -> Charlie REJECTS.
   (Charlie independently chose bases; Bob's fabrication produces mismatch rate ~0.50,
   preventing verifier forgery across different recipients).
8. Dual-threshold transferability policy evaluates primary and secondary verifiers.
"""
import pytest
from fastapi.testclient import TestClient
import time
import uuid

from apps.api.main import app
from src.security.envelope import PQCEnvelope
from src.security.identity import global_pqc_identity
from src.keyvault.session_store import global_session_store
from src.detection.policy import global_policy


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def transfer_setup():
    alice_pk, alice_sk = PQCEnvelope.generate_keypair()
    global_pqc_identity.register_participant("alice_transfer", alice_pk, is_verifier=False, role="verifier")
    global_pqc_identity.register_participant("bob_transfer", alice_pk, is_verifier=True, role="verifier")
    global_pqc_identity.register_participant("charlie_transfer", alice_pk, is_verifier=True, role="verifier")
    
    return {
        "alice_sk": alice_sk,
        "signer_id": "alice_transfer",
        "bob": "bob_transfer",
        "charlie": "charlie_transfer"
    }


def _prepare_transferability_fabrication(client, transfer_setup, L=120):
    session_id = f"test-transfer-{uuid.uuid4()}"
    dist_payload = {
        "session_id": session_id,
        "signer_id": transfer_setup["signer_id"],
        "verifiers": [transfer_setup["bob"], transfer_setup["charlie"]],
        "L": L,
        "nonce": f"nonce-dist-{uuid.uuid4()}",
        "timestamp": time.time()
    }
    dist_payload["signature"] = PQCEnvelope.sign_payload(transfer_setup["alice_sk"], dist_payload)
    res_dist = client.post("/v1/qds/distribute", json=dist_payload)
    assert res_dist.status_code == 200, res_dist.text

    v_data = global_session_store.get_verifier_outcomes(session_id, transfer_setup["bob"])
    assert v_data is not None, "Bob outcomes not found"
    bob_bases, bob_outcomes = v_data
    
    fabricated_keys = [
        {"bit_index": i, "basis": bob_bases[i], "bit_value": bob_outcomes[i]}
        for i in range(len(bob_bases))
    ]
    return session_id, fabricated_keys


def test_bob_fabrication_accepts_at_bob(client, transfer_setup):
    """Test 6: Bob fabricates from his own records -> Bob ACCEPTS (expected zero mismatch)."""
    session_id, fabricated_keys = _prepare_transferability_fabrication(client, transfer_setup)
    
    ver_payload_bob = {
        "session_id": session_id,
        "signer_id": transfer_setup["signer_id"],
        "verifier_id": transfer_setup["bob"],
        "nonce": f"nonce-ver-bob-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": 0,
        "revealed_keys": fabricated_keys
    }
    ver_payload_bob["signature"] = PQCEnvelope.sign_payload(transfer_setup["alice_sk"], ver_payload_bob)
    res_bob = client.post("/v1/qds/verify", json=ver_payload_bob)
    assert res_bob.status_code == 200
    data_bob = res_bob.json()
    assert data_bob["decision"] == "ACCEPT", f"Expected Bob to accept his own fabrication, got {data_bob['decision']}"


def test_same_fabrication_submitted_to_charlie_rejects(client, transfer_setup):
    """Test 7: The exact same fabrication submitted to Charlie -> Charlie REJECTS."""
    session_id, fabricated_keys = _prepare_transferability_fabrication(client, transfer_setup)
    
    ver_payload_charlie = {
        "session_id": session_id,
        "signer_id": transfer_setup["signer_id"],
        "verifier_id": transfer_setup["charlie"],
        "nonce": f"nonce-ver-charlie-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": 0,
        "revealed_keys": fabricated_keys
    }
    ver_payload_charlie["signature"] = PQCEnvelope.sign_payload(transfer_setup["alice_sk"], ver_payload_charlie)
    res_charlie = client.post("/v1/qds/verify", json=ver_payload_charlie)
    assert res_charlie.status_code == 200
    data_charlie = res_charlie.json()
    assert data_charlie["decision"] == "REJECT", f"Expected Charlie to reject Bob's fabrication, got {data_charlie['decision']}"


def test_dual_threshold_transferability_policy():
    """Test dual-threshold evaluation method evaluate_transferable in policy."""
    tau_low, tau_high = global_policy.get_thresholds()
    
    # Primary below tau_low and secondary below tau_high -> ACCEPT
    res_accept = global_policy.evaluate_transferable(tau_low * 0.5, tau_high * 0.5)
    assert res_accept.decision == "ACCEPT"
    assert len(res_accept.findings) == 0

    # Primary below tau_low but secondary above tau_high (transferability forgery) -> REJECT
    res_reject = global_policy.evaluate_transferable(0.0, 0.50)
    assert res_reject.decision == "REJECT"
    assert len(res_reject.findings) == 1
    assert res_reject.findings[0].detector_name == "TransferabilityDetector"
