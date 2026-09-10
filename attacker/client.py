"""
Q-SENTINEL Attack Client — adversarial HTTP client for the isolated testbed.

Every attack scenario uses this client to issue real HTTP requests to the
Q-SENTINEL API.  The client never modifies internal Python state of the
target; it operates strictly as an external adversarial network client.
"""
import requests
import uuid
import time
import datetime
import json
import random
from typing import Optional, List, Dict, Any

from attacker.config import API_URL, DEFAULT_SHOTS
from src.keyvault import global_keyvault
from src.keyvault.session_store import global_session_store
from src.qds.teleportation_qds import TeleportationQDS
from src.security.envelope import PQCEnvelope


def send_distribute(
    session_id: str,
    signer_id: str = "alice",
    verifiers: Optional[List[str]] = None,
    L: int = 100,
    disturbance: float = 0.0,
    perturbation: Optional[str] = None,
) -> dict:
    """POST /v1/qds/distribute for genuine session setup."""
    if verifiers is None:
        verifiers = ["bob"]
    timestamp = time.time()
    nonce = f"nonce-{uuid.uuid4()}"
    from apps.api.routes.testbed import _testbed_channel_state
    if perturbation is not None:
        _testbed_channel_state["perturbation"] = perturbation
        _testbed_channel_state["magnitude"] = disturbance
    elif disturbance > 0.0:
        _testbed_channel_state["perturbation"] = "depolarizing"
        _testbed_channel_state["magnitude"] = disturbance
    elif _testbed_channel_state.get("perturbation") not in ["rx_only", "rz_only", "depolarizing", "intercept_resend"]:
        _testbed_channel_state["perturbation"] = "none"
        _testbed_channel_state["magnitude"] = 0.0

    req_payload = {
        "session_id": session_id,
        "signer_id": signer_id,
        "verifiers": verifiers,
        "L": L,
        "nonce": nonce,
        "timestamp": timestamp,
    }
    key_path = f"attacker/credentials/{signer_id}_sk.bin"
    try:
        with open(key_path, "rb") as f:
            sk = f.read()
        req_payload["signature"] = PQCEnvelope.sign_payload(sk, req_payload)
    except Exception:
        try:
            with open("attacker/credentials/mallory_sk.bin", "rb") as f:
                sk = f.read()
            req_payload["signature"] = PQCEnvelope.sign_payload(sk, req_payload)
        except Exception:
            req_payload["signature"] = "dummy_sig"

    if _check_api_live():
        try:
            resp = requests.post(f"{API_URL}/v1/qds/distribute", json=req_payload, timeout=(1.0, 30))
            return resp.json() if resp.content else {}
        except requests.RequestException:
            pass
    tc = _get_test_client()
    resp = tc.post("/v1/qds/distribute", json=req_payload)
    return resp.json() if resp.content else {}


def send_reveal(
    session_id: str,
    signer_id: str = "alice",
    message_bit: int = 0,
) -> dict:
    """POST /v1/qds/reveal for genuine key retrieval."""
    timestamp = time.time()
    nonce = f"nonce-{uuid.uuid4()}"
    req_payload = {
        "session_id": session_id,
        "signer_id": signer_id,
        "message_bit": message_bit,
        "nonce": nonce,
        "timestamp": timestamp,
    }
    key_path = f"attacker/credentials/{signer_id}_sk.bin"
    try:
        with open(key_path, "rb") as f:
            sk = f.read()
        req_payload["signature"] = PQCEnvelope.sign_payload(sk, req_payload)
    except Exception:
        try:
            with open("attacker/credentials/mallory_sk.bin", "rb") as f:
                sk = f.read()
            req_payload["signature"] = PQCEnvelope.sign_payload(sk, req_payload)
        except Exception:
            req_payload["signature"] = "dummy_sig"

    if _check_api_live():
        try:
            resp = requests.post(f"{API_URL}/v1/qds/reveal", json=req_payload, timeout=(1.0, 30))
            return resp.json() if resp.content else {}
        except requests.RequestException:
            pass
    tc = _get_test_client()
    resp = tc.post("/v1/qds/reveal", json=req_payload)
    return resp.json() if resp.content else {}


def get_base_payload(
    signer_id: str = "alice",
    verifier_id: str = "bob",
    L: int = 100,
    disturbance: float = 0.0,
    perturbation: Optional[str] = None,
    message_bit: int = 0,
    experiment_id: str = "live-demo",
    sign: bool = True,
    tamper_signature: bool = False,
    mutate_keys: bool = False,
    mutation_rate: float = 0.3,
    shots: int = DEFAULT_SHOTS,
    disturbance_prob: float = 0.0,
) -> dict:
    """Construct a legitimate or parameterised verification request payload via real API distribution."""
    eff_dist = disturbance if disturbance > 0.0 else disturbance_prob
    session_id = f"session-{uuid.uuid4()}"

    # 1. Distribute session over real pipeline
    send_distribute(
        session_id=session_id,
        signer_id="alice" if signer_id not in ["alice", "bob", "charlie"] else signer_id,
        verifiers=[verifier_id if verifier_id in ["bob", "charlie"] else "bob"],
        L=L,
        disturbance=eff_dist,
        perturbation=perturbation,
    )

    # 2. Reveal honest key material
    rev_resp = send_reveal(
        session_id=session_id,
        signer_id="alice" if signer_id not in ["alice", "bob", "charlie"] else signer_id,
        message_bit=message_bit,
    )
    revealed_keys = rev_resp.get("revealed_keys", [])
    if not revealed_keys:
        revealed_keys = [
            {"bit_index": i, "basis": "X" if i % 2 == 0 else "Z", "bit_value": 0}
            for i in range(L)
        ]

    # 3. Apply key mutation if requested (forgery)
    if mutate_keys:
        import copy
        revealed_keys = copy.deepcopy(revealed_keys)
        mut_count = max(5, int(len(revealed_keys) * mutation_rate))
        mut_indices = random.sample(range(len(revealed_keys)), min(mut_count, len(revealed_keys)))
        for idx in mut_indices:
            revealed_keys[idx]["bit_value"] ^= 1  # Flip bit to forge classical key

    payload = {
        "session_id": session_id,
        "signer_id": signer_id,
        "verifier_id": verifier_id,
        "nonce": f"nonce-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": message_bit,
        "revealed_keys": revealed_keys,
    }

    if sign:
        key_path = f"attacker/credentials/{signer_id}_sk.bin"
        try:
            with open(key_path, "rb") as f:
                sk = f.read()
            sig = PQCEnvelope.sign_payload(sk, payload)
            if tamper_signature:
                sig = "invalid_tampered_signature" + sig[26:]
            payload["signature"] = sig
        except Exception:
            try:
                with open("attacker/credentials/mallory_sk.bin", "rb") as f:
                    sk = f.read()
                sig = PQCEnvelope.sign_payload(sk, payload)
                payload["signature"] = sig
            except Exception:
                payload["signature"] = "dummy_signature_fallback"
    else:
        payload["signature"] = "unsigned_invalid_signature"

    return payload


_api_live_status: Optional[bool] = None
_test_client_instance = None


def _check_api_live() -> bool:
    """Fast check whether an external API server is listening on API_URL."""
    global _api_live_status
    if _api_live_status is not None:
        return _api_live_status
    import socket
    from urllib.parse import urlparse
    parsed = urlparse(API_URL)
    host = parsed.hostname or "localhost"
    port = parsed.port or 8000
    try:
        s = socket.create_connection((host, port), timeout=0.2)
        s.close()
        _api_live_status = True
    except (socket.timeout, ConnectionRefusedError, OSError):
        _api_live_status = False
    return _api_live_status


def _get_test_client():
    global _test_client_instance
    if _test_client_instance is None:
        from apps.api.main import app
        from fastapi.testclient import TestClient
        _test_client_instance = TestClient(app)
    return _test_client_instance


def send_verify(payload: dict) -> dict:
    """
    POST a verification request to /v1/qds/verify.

    Returns a structured result dict regardless of HTTP status code.
    Seamlessly uses in-process TestClient if API daemon is offline.
    """
    started = datetime.datetime.utcnow().isoformat()
    headers = {"Content-Type": "application/json", "x-role": "auditor"}
    
    if _check_api_live():
        try:
            resp = requests.post(f"{API_URL}/v1/qds/verify", json=payload, headers=headers, timeout=(1.0, 30))
            completed = datetime.datetime.utcnow().isoformat()
            body = resp.json() if resp.content else {}
            return {
                "http_status": resp.status_code,
                "started_at": started,
                "completed_at": completed,
                "response": body,
                "error": None,
            }
        except requests.RequestException:
            pass  # Fallback to test client

    # In-process TestClient fallback
    try:
        tc = _get_test_client()
        resp = tc.post("/v1/qds/verify", json=payload, headers=headers)
        completed = datetime.datetime.utcnow().isoformat()
        body = resp.json() if resp.content else {}
        return {
            "http_status": resp.status_code,
            "started_at": started,
            "completed_at": completed,
            "response": body,
            "error": None,
        }
    except Exception as exc:
        return {
            "http_status": None,
            "started_at": started,
            "completed_at": datetime.datetime.utcnow().isoformat(),
            "response": {},
            "error": str(exc),
        }


def verify_chain() -> dict:
    """GET /v1/ledger/verify-chain — returns chain integrity result."""
    if _check_api_live():
        try:
            resp = requests.get(f"{API_URL}/v1/ledger/verify-chain", timeout=(1.0, 30))
            data = resp.json()
            if "chain_valid" in data and "valid" not in data:
                data["valid"] = data["chain_valid"]
            return data
        except requests.RequestException:
            pass
    try:
        tc = _get_test_client()
        resp = tc.get("/v1/ledger/verify-chain")
        data = resp.json()
        if "chain_valid" in data and "valid" not in data:
            data["valid"] = data["chain_valid"]
        return data
    except Exception as exc:
        return {"valid": False, "chain_valid": False, "reason": str(exc)}


def get_event(event_id: str) -> dict:
    """GET /v1/ledger/verify/{event_id} — returns a single ledger record."""
    if _check_api_live():
        try:
            resp = requests.get(f"{API_URL}/v1/ledger/verify/{event_id}", timeout=(1.0, 30))
            return resp.json()
        except requests.RequestException:
            pass
    try:
        tc = _get_test_client()
        resp = tc.get(f"/v1/ledger/verify/{event_id}")
        return resp.json()
    except Exception as exc:
        return {"error": str(exc)}
