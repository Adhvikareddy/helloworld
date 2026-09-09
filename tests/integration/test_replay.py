"""
Integration tests for replay protection and session persistence (T5).

Tests:
8. Reusing a nonce -> REJECT.
9. Reusing a consumed session for the same verifier -> REJECT.
10a. Nonce replay protection survives recreating the SQLite store object (persistence).
10b. Session double-consumption protection survives recreating the SQLite store object (persistence).
"""
import pytest
from fastapi.testclient import TestClient
import time
import uuid

from apps.api.main import app
from src.security.envelope import PQCEnvelope
from src.security.identity import global_pqc_identity
from src.security.nonce import SQLiteNonceGuard
from src.keyvault.session_store import SessionStore


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def replay_setup():
    alice_pk, alice_sk = PQCEnvelope.generate_keypair()
    global_pqc_identity.register_participant("alice_replay", alice_pk, is_verifier=False, role="verifier")
    global_pqc_identity.register_participant("bob_replay", alice_pk, is_verifier=True, role="verifier")
    
    return {
        "alice_sk": alice_sk,
        "signer_id": "alice_replay",
        "verifier_id": "bob_replay"
    }


def _create_and_reveal_session(client, setup, L=30):
    session_id = f"test-replay-{uuid.uuid4()}"
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


def test_reusing_nonce_rejects(client, replay_setup):
    """Test 8: Reusing a nonce -> REJECT."""
    session_id, legit_keys = _create_and_reveal_session(client, replay_setup)
    reused_nonce = f"shared-nonce-{uuid.uuid4()}"
    
    ver_payload_1 = {
        "session_id": session_id,
        "signer_id": replay_setup["signer_id"],
        "verifier_id": replay_setup["verifier_id"],
        "nonce": reused_nonce,
        "timestamp": time.time(),
        "message_bit": 0,
        "revealed_keys": legit_keys
    }
    ver_payload_1["signature"] = PQCEnvelope.sign_payload(replay_setup["alice_sk"], ver_payload_1)
    res_1 = client.post("/v1/qds/verify", json=ver_payload_1)
    assert res_1.status_code == 200
    assert res_1.json()["decision"] == "ACCEPT"

    ver_payload_2 = {
        "session_id": session_id,
        "signer_id": replay_setup["signer_id"],
        "verifier_id": replay_setup["verifier_id"],
        "nonce": reused_nonce,
        "timestamp": time.time(),
        "message_bit": 0,
        "revealed_keys": legit_keys
    }
    ver_payload_2["signature"] = PQCEnvelope.sign_payload(replay_setup["alice_sk"], ver_payload_2)
    res_2 = client.post("/v1/qds/verify", json=ver_payload_2)
    assert res_2.status_code == 200
    assert res_2.json()["decision"] == "REJECT"


def test_reusing_consumed_session_for_same_verifier_rejects(client, replay_setup):
    """Test 9: Reusing a consumed session for the same verifier -> REJECT."""
    session_id, legit_keys = _create_and_reveal_session(client, replay_setup)
    
    ver_payload_1 = {
        "session_id": session_id,
        "signer_id": replay_setup["signer_id"],
        "verifier_id": replay_setup["verifier_id"],
        "nonce": f"nonce-first-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": 0,
        "revealed_keys": legit_keys
    }
    ver_payload_1["signature"] = PQCEnvelope.sign_payload(replay_setup["alice_sk"], ver_payload_1)
    res_1 = client.post("/v1/qds/verify", json=ver_payload_1)
    assert res_1.status_code == 200
    assert res_1.json()["decision"] == "ACCEPT"

    ver_payload_2 = {
        "session_id": session_id,
        "signer_id": replay_setup["signer_id"],
        "verifier_id": replay_setup["verifier_id"],
        "nonce": f"nonce-fresh-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": 0,
        "revealed_keys": legit_keys
    }
    ver_payload_2["signature"] = PQCEnvelope.sign_payload(replay_setup["alice_sk"], ver_payload_2)
    res_2 = client.post("/v1/qds/verify", json=ver_payload_2)
    assert res_2.status_code == 200
    assert res_2.json()["decision"] == "REJECT"


def test_nonce_guard_persistence_across_instances(tmp_path):
    """Test 10a: Nonce replay protection survives recreating the SQLite store object."""
    nonce_db = str(tmp_path / "test_nonces.db")
    guard1 = SQLiteNonceGuard(db_path=nonce_db)
    test_nonce = f"test-nonce-{uuid.uuid4()}"
    test_session = "test-session-persist"
    assert guard1.is_fresh(test_nonce, test_session) is True
    assert guard1.is_fresh(test_nonce, test_session) is False
    
    # Recreate guard instance on the same SQLite file
    guard2 = SQLiteNonceGuard(db_path=nonce_db)
    assert guard2.is_fresh(test_nonce, test_session) is False


def test_session_store_consumption_persistence_across_instances(tmp_path):
    """Test 10b: Session consumption protection survives recreating the SQLite store object."""
    session_db = str(tmp_path / "test_sessions.db")
    store1 = SessionStore(db_path=session_db)
    store1.create_session_record("sess-persist", "alice", 30, time.time())
    assert store1.is_consumed("sess-persist", "bob") is False
    store1.mark_consumed("sess-persist", "bob", time.time())
    assert store1.is_consumed("sess-persist", "bob") is True

    # Recreate store instance on the same SQLite file
    store2 = SessionStore(db_path=session_db)
    assert store2.is_consumed("sess-persist", "bob") is True
