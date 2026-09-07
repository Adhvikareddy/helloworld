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
from typing import Optional
from attacker.config import API_URL, DEFAULT_SHOTS


def get_base_payload(
    signer_id: str = "alice",
    verifier_id: str = "bob",
    shots: int = DEFAULT_SHOTS,
    experiment_id: str = "live-demo",
) -> dict:
    """Construct a legitimate verification request payload."""
    return {
        "session_id": f"sess-{uuid.uuid4()}",
        "signer_id": signer_id,
        "verifier_id": verifier_id,
        "nonce": f"nonce-{uuid.uuid4()}",
        "measurement_bases": ["X", "Y", "Z"],
        "shots": shots,
        "signature": "valid_signature_hash",
        "message_digest": "valid_message_digest",
        "timestamp": time.time(),
        "is_invalid_signature": False,
        "disturbance_prob": 0.0,
        "experiment_id": experiment_id,
    }


def send_verify(payload: dict) -> dict:
    """
    POST a verification request to /v1/qds/verify.

    Returns a structured result dict regardless of HTTP status code.
    """
    started = datetime.datetime.utcnow().isoformat()
    try:
        resp = requests.post(f"{API_URL}/v1/qds/verify", json=payload, timeout=120)
        completed = datetime.datetime.utcnow().isoformat()
        body = resp.json() if resp.content else {}
        return {
            "http_status": resp.status_code,
            "started_at": started,
            "completed_at": completed,
            "response": body,
            "error": None,
        }
    except requests.RequestException as exc:
        return {
            "http_status": None,
            "started_at": started,
            "completed_at": datetime.datetime.utcnow().isoformat(),
            "response": {},
            "error": str(exc),
        }


def verify_chain() -> dict:
    """GET /v1/ledger/verify-chain — returns chain integrity result."""
    try:
        resp = requests.get(f"{API_URL}/v1/ledger/verify-chain", timeout=30)
        return resp.json()
    except requests.RequestException as exc:
        return {"valid": None, "reason": str(exc)}


def get_event(event_id: str) -> dict:
    """GET /v1/ledger/verify/{event_id} — returns a single ledger record."""
    try:
        resp = requests.get(f"{API_URL}/v1/ledger/verify/{event_id}", timeout=30)
        return resp.json()
    except requests.RequestException as exc:
        return {"error": str(exc)}
