"""
Scenario: Forgery by Verifier (Transferability Attack).

Demonstrates QDS transferability (why QDS is a signature, not just a MAC):
Bob fabricates revealed keys claiming exactly his own measured basis and outcome
at each position.
When submitted to Bob, Bob ACCEPTS (expected: mismatch rate = 0).
When the exact same fabrication is submitted to Charlie, Charlie REJECTS
(mismatch rate ~ 0.5 because Charlie chose bases independently).
"""
import uuid
import time
from typing import Dict, Any, List

from attacker.client import send_distribute, send_verify
from src.keyvault.session_store import global_session_store
from src.security.envelope import PQCEnvelope


def run_forgery_by_verifier(L: int = 100) -> Dict[str, Any]:
    """
    Execute forgery by verifier transferability scenario.
    
    1. Distribute a valid QDS session to both Bob and Charlie.
    2. Read Bob's stored outcomes via global_session_store.get_verifier_outcomes.
    3. Fabricate revealed keys using Bob's records.
    4. Submit verification for verifier_id="bob" -> Expect ACCEPT.
    5. Submit verification for verifier_id="charlie" -> Expect REJECT.
    6. Report both decisions.
    """
    session_id = f"session-transferability-{uuid.uuid4()}"
    
    # Load Alice's private key for signing verification requests
    with open("attacker/credentials/alice_sk.bin", "rb") as f:
        alice_sk = f.read()
        
    # 1. Distribute to both Bob and Charlie
    send_distribute(
        session_id=session_id,
        signer_id="alice",
        verifiers=["bob", "charlie"],
        L=L,
        disturbance=0.0
    )
    
    # 2. Read Bob's stored outcomes
    v_data = global_session_store.get_verifier_outcomes(session_id, "bob")
    if not v_data:
        raise RuntimeError(f"Could not retrieve verifier outcomes for bob in session {session_id}")
        
    bob_bases, bob_outcomes = v_data
    
    # 3. Build revealed keys claiming Bob's bases and outcomes
    revealed_keys = [
        {"bit_index": i, "basis": bob_bases[i], "bit_value": bob_outcomes[i]}
        for i in range(len(bob_bases))
    ]
    
    # 4. Verify against Bob
    payload_bob = {
        "session_id": session_id,
        "signer_id": "alice",
        "verifier_id": "bob",
        "nonce": f"nonce-ver-bob-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": 0,
        "revealed_keys": revealed_keys
    }
    payload_bob["signature"] = PQCEnvelope.sign_payload(alice_sk, payload_bob)
    raw_bob = send_verify(payload_bob)
    decision_bob = raw_bob["response"].get("decision", "ERROR")
    
    # 5. Verify against Charlie
    payload_charlie = {
        "session_id": session_id,
        "signer_id": "alice",
        "verifier_id": "charlie",
        "nonce": f"nonce-ver-charlie-{uuid.uuid4()}",
        "timestamp": time.time(),
        "message_bit": 0,
        "revealed_keys": revealed_keys
    }
    payload_charlie["signature"] = PQCEnvelope.sign_payload(alice_sk, payload_charlie)
    raw_charlie = send_verify(payload_charlie)
    decision_charlie = raw_charlie["response"].get("decision", "ERROR")
    
    # 6. Report decisions
    print(f"verifier=bob -> {decision_bob}")
    print(f"verifier=charlie -> {decision_charlie}")
    
    return {
        "session_id": session_id,
        "decision_bob": decision_bob,
        "decision_charlie": decision_charlie,
        "transferability_preserved": (decision_bob == "ACCEPT" and decision_charlie == "REJECT"),
        "response_bob": raw_bob["response"],
        "response_charlie": raw_charlie["response"]
    }
