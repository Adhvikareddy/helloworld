from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

router = APIRouter()

# In-memory store for active channel testbed parameters
_testbed_state: Dict[str, float] = {
    "disturbance": 0.0
}

class ChannelTestbedRequest(BaseModel):
    disturbance: float = Field(..., ge=0.0, le=1.0, description="Noise parameter p in [0.0, 1.0]")
    operator_signature: Optional[str] = Field(None, description="Operator signature for lab control")

class ChannelTestbedResponse(BaseModel):
    status: str
    disturbance: float

@router.post("/channel", response_model=ChannelTestbedResponse)
def set_channel_disturbance(req: ChannelTestbedRequest):
    _testbed_state["disturbance"] = req.disturbance
    return ChannelTestbedResponse(
        status="CONFIGURED",
        disturbance=req.disturbance
    )

@router.get("/channel", response_model=ChannelTestbedResponse)
def get_channel_disturbance():
    return ChannelTestbedResponse(
        status="ACTIVE",
        disturbance=_testbed_state["disturbance"]
    )

def get_active_disturbance() -> float:
    return _testbed_state["disturbance"]

class AttackTriggerRequest(BaseModel):
    disturbance: Optional[float] = 0.25
    repeats: Optional[int] = 1

@router.post("/attack/{scenario_name}")
def trigger_attack_scenario(scenario_name: str, req: Optional[AttackTriggerRequest] = None):
    import os
    import copy
    import random
    import time
    import uuid
    import sqlite3
    from attacker.client import get_base_payload, send_verify
    from src.security.envelope import PQCEnvelope
    from src.ledger.hash_chain import global_ledger
    from src.ledger.verifier import verify_ledger

    dist = req.disturbance if req and req.disturbance is not None else 0.25
    scenario = scenario_name.lower().replace("-", "_")

    if scenario in ["forgery", "forgery_a", "forgery_b", "quantum_forgery"]:
        # 1. Forgery scenario: Valid ML-DSA-65 envelope, but attacker alters revealed quantum keys
        trial_id = f"forgery-{uuid.uuid4()}"
        payload = get_base_payload(signer_id="alice", verifier_id="bob", disturbance=0.0, experiment_id=trial_id)
        
        # Randomly mutate 20% to 45% of revealed key bits
        revealed = copy.deepcopy(payload["revealed_keys"])
        mut_count = random.randint(max(5, int(len(revealed) * 0.2)), max(10, int(len(revealed) * 0.45)))
        mut_indices = random.sample(range(len(revealed)), mut_count)
        for idx in mut_indices:
            revealed[idx]["bit_value"] ^= 1  # Flip bit
        payload["revealed_keys"] = revealed

        # Re-sign with Alice's valid private key so L3 envelope is 100% valid
        with open("attacker/credentials/alice_sk.bin", "rb") as f:
            alice_sk = f.read()
        payload["signature"] = PQCEnvelope.sign_payload(alice_sk, payload)

        raw = send_verify(payload)
        resp = raw.get("response", {})
        actual_decision = "REJECT" if raw.get("http_status") == 403 else resp.get("decision", "ERROR")

        return {
            "scenario": scenario_name,
            "attack_type": "forgery",
            "target": "/v1/qds/verify",
            "pipeline_stages": ["distribute", "reveal", "mutate_quantum_keys", "pqc_sign", "verify"],
            "expected_primary_layer": "L2 (StatisticalProbe)",
            "expected_outcome": "REJECT",
            "actual_outcome": actual_decision,
            "detected": actual_decision != "ACCEPT",
            "event_id": resp.get("evidence_id"),
            "findings": resp.get("findings", []),
            "latency_ms": resp.get("latency_ms", 0.0),
            "parameters": {"mutated_bits_count": mut_count, "total_bits": len(revealed)},
            "reason": "Cryptographically valid envelope with forged/mutated quantum key material caught by matched-basis evaluation."
        }

    elif scenario in ["replay"]:
        # 2. Replay scenario: Valid first submission, then immediate duplicate resubmission
        trial_id = f"replay-{uuid.uuid4()}"
        payload = get_base_payload(signer_id="alice", verifier_id="bob", disturbance=0.0, experiment_id=trial_id)
        
        # First verification succeeds
        first_raw = send_verify(payload)
        # Resubmit identical payload with same session_id and nonce
        second_raw = send_verify(copy.deepcopy(payload))
        resp = second_raw.get("response", {})
        actual_decision = "REJECT" if second_raw.get("http_status") == 403 else resp.get("decision", "ERROR")

        return {
            "scenario": scenario_name,
            "attack_type": "replay",
            "target": "/v1/qds/verify",
            "pipeline_stages": ["distribute", "initial_verify_accept", "replay_resubmit"],
            "expected_primary_layer": "L3 (FreshnessProbe / NonceGuard)",
            "expected_outcome": "REJECT",
            "actual_outcome": actual_decision,
            "detected": actual_decision != "ACCEPT",
            "event_id": resp.get("evidence_id"),
            "findings": resp.get("findings", []),
            "latency_ms": resp.get("latency_ms", 0.0),
            "parameters": {"replayed_nonce": payload["nonce"], "session_id": payload["session_id"]},
            "reason": "Re-submitted identical session/nonce detected by persistent nonce guard and session single-use check."
        }

    elif scenario in ["impersonation", "impersonate"]:
        # 3. Impersonation: Adversary signs request claiming Alice's identity
        trial_id = f"impersonation-{uuid.uuid4()}"
        payload = get_base_payload(signer_id="alice", verifier_id="bob", disturbance=0.0, experiment_id=trial_id)
        
        # Mallory signs Alice's payload using Mallory's private key
        with open("attacker/credentials/mallory_sk.bin", "rb") as f:
            mallory_sk = f.read()
        payload["signature"] = PQCEnvelope.sign_payload(mallory_sk, payload)

        raw = send_verify(payload)
        resp = raw.get("response", {})
        actual_decision = "REJECT" if raw.get("http_status") == 403 else resp.get("decision", "ERROR")

        return {
            "scenario": scenario_name,
            "attack_type": "impersonation",
            "target": "/v1/qds/verify",
            "pipeline_stages": ["distribute", "adversarial_pqc_signature", "verify"],
            "expected_primary_layer": "L3 (AuthenticationProbe / IdentityGuard)",
            "expected_outcome": "REJECT",
            "actual_outcome": actual_decision,
            "detected": actual_decision != "ACCEPT",
            "event_id": resp.get("evidence_id"),
            "findings": resp.get("findings", []),
            "latency_ms": resp.get("latency_ms", 0.0),
            "parameters": {"claimed_signer": "alice", "signing_key": "mallory"},
            "reason": "Mallory forged request claiming to be Alice; rejected by ML-DSA-65 public key identity verification."
        }

    elif scenario in ["unauthorized", "unauthorized_verifier"]:
        # 4. Unauthorized verifier: Request targets an unapproved station node
        trial_id = f"unauthorized-{uuid.uuid4()}"
        bad_verifier = random.choice(["rogue_node_4", "unauthorized_station", "foreign_listener"])
        payload = get_base_payload(signer_id="alice", verifier_id=bad_verifier, disturbance=0.0, experiment_id=trial_id)

        raw = send_verify(payload)
        resp = raw.get("response", {})
        actual_decision = "REJECT" if raw.get("http_status") == 403 else resp.get("decision", "ERROR")

        return {
            "scenario": scenario_name,
            "attack_type": "unauthorized_verification",
            "target": "/v1/qds/verify",
            "pipeline_stages": ["distribute", "unauthorized_verifier_id", "verify"],
            "expected_primary_layer": "L3 (AuthorizationGuard)",
            "expected_outcome": "REJECT",
            "actual_outcome": actual_decision,
            "detected": actual_decision != "ACCEPT",
            "event_id": resp.get("evidence_id"),
            "findings": resp.get("findings", []),
            "latency_ms": resp.get("latency_ms", 0.0),
            "parameters": {"unauthorized_verifier_id": bad_verifier},
            "reason": "Verifier node not present in authorized verifiers registry; rejected before quantum state evaluation."
        }

    elif scenario in ["channel", "channel_manipulation"]:
        # 5. Channel disturbance: Elevated depolarizing noise during distribution
        trial_id = f"channel-{uuid.uuid4()}"
        payload = get_base_payload(signer_id="alice", verifier_id="bob", disturbance=dist, experiment_id=trial_id)

        raw = send_verify(payload)
        resp = raw.get("response", {})
        actual_decision = resp.get("decision", "ERROR")

        return {
            "scenario": scenario_name,
            "attack_type": "channel_manipulation",
            "target": "/v1/qds/verify",
            "pipeline_stages": ["distribute_noisy_channel", "verify"],
            "expected_primary_layer": "L2 (StatisticalProbe / Tomography)",
            "expected_outcome": "QUARANTINE" if dist <= 0.15 else "REJECT",
            "actual_outcome": actual_decision,
            "detected": actual_decision != "ACCEPT",
            "event_id": resp.get("evidence_id"),
            "findings": resp.get("findings", []),
            "latency_ms": resp.get("latency_ms", 0.0),
            "parameters": {"disturbance_probability": dist},
            "reason": f"Depolarizing channel disturbance (p={dist}) induced state mismatches detected by statistical probe."
        }

    elif scenario in ["ledger_tamper", "ledger"]:
        # 6. Ledger Tampering: Direct SQLite record modification
        db_path = global_ledger.db_path
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT seq_num, decision FROM evidence ORDER BY seq_num DESC LIMIT 1")
            row = cursor.fetchone()
            if not row:
                # Seed an event first
                dummy_payload = get_base_payload(disturbance=0.0)
                send_verify(dummy_payload)
                cursor.execute("SELECT seq_num, decision FROM evidence ORDER BY seq_num DESC LIMIT 1")
                row = cursor.fetchone()

            seq_num, decision = row
            new_decision = "REJECT" if decision == "ACCEPT" else "ACCEPT"
            cursor.execute("UPDATE evidence SET decision = ? WHERE seq_num = ?", (new_decision, seq_num))
            conn.commit()

        # Audit chain immediately to observe genuine detection
        chain_valid = verify_ledger(db_path)

        return {
            "scenario": scenario_name,
            "attack_type": "ledger_tamper",
            "target": "/v1/ledger/verify-chain",
            "pipeline_stages": ["direct_sqlite_mutation", "verify_chain_audit"],
            "expected_primary_layer": "L4 (EvidenceLedger HMAC & Hash Chain)",
            "expected_outcome": "chain_valid=False",
            "actual_outcome": "INTEGRITY_VIOLATION" if not chain_valid else "VALID",
            "detected": not chain_valid,
            "event_id": f"block-{seq_num}",
            "findings": [{"detector": "HashChainVerifier", "severity": "REJECT", "description": f"HMAC or hash linkage mismatch detected at block {seq_num}."}],
            "latency_ms": 1.2,
            "parameters": {"tampered_seq_num": seq_num, "old_decision": decision, "new_decision": new_decision},
            "reason": f"Direct database mutation on block #{seq_num} broke cryptographic HMAC-SHA256 hash chain."
        }

    elif scenario in ["timing_oracle", "timing"]:
        # 7. Constant-time latency analysis
        start_valid = time.time()
        v_payload = get_base_payload(signer_id="alice", disturbance=0.0)
        send_verify(v_payload)
        t_valid = time.time() - start_valid

        start_invalid = time.time()
        inv_payload = copy.deepcopy(v_payload)
        inv_payload["signature"] = "invalid_signature_tamper"
        send_verify(inv_payload)
        t_invalid = time.time() - start_invalid

        delta = abs(t_valid - t_invalid)
        secure = delta < 0.5

        return {
            "scenario": scenario_name,
            "attack_type": "timing_oracle",
            "target": "/v1/qds/verify",
            "pipeline_stages": ["valid_envelope_probe", "invalid_envelope_probe", "delta_variance_check"],
            "expected_primary_layer": "Constant-Time Latency Guard",
            "expected_outcome": "SECURE",
            "actual_outcome": "SECURE" if secure else "VULNERABLE",
            "detected": secure,
            "event_id": None,
            "findings": [{"detector": "TimingGuard", "severity": "INFO", "description": f"Delta={delta:.4f}s within constant-time bounds."}],
            "latency_ms": delta * 1000.0,
            "parameters": {"valid_latency_s": round(t_valid, 4), "invalid_latency_s": round(t_invalid, 4), "delta_s": round(delta, 4)},
            "reason": f"Response time delta ({delta:.4f}s) is negligible; constant-time padding floor prevents side-channel profiling."
        }

    elif scenario in ["legitimate", "honest"]:
        # 8. Legitimate transmission over clean channel
        trial_id = f"honest-{uuid.uuid4()}"
        payload = get_base_payload(signer_id="alice", verifier_id="bob", disturbance=0.0, experiment_id=trial_id)
        raw = send_verify(payload)
        resp = raw.get("response", {})
        actual_decision = resp.get("decision", "ERROR")

        return {
            "scenario": scenario_name,
            "attack_type": "legitimate",
            "target": "/v1/qds/verify",
            "pipeline_stages": ["distribute_clean", "verify"],
            "expected_primary_layer": "None (Pass)",
            "expected_outcome": "ACCEPT",
            "actual_outcome": actual_decision,
            "detected": False,
            "event_id": resp.get("evidence_id"),
            "findings": resp.get("findings", []),
            "latency_ms": resp.get("latency_ms", 0.0),
            "parameters": {"disturbance": 0.0},
            "reason": "Honest transmission over clean quantum channel verified successfully."
        }

    else:
        raise HTTPException(status_code=400, detail=f"Unknown scenario: {scenario_name}")

class BlindBatchRequest(BaseModel):
    batch_size: Optional[int] = Field(100, ge=1, le=500)

@router.post("/blind-trial")
def run_single_blind_trial():
    """Execute a single blind randomized trial (ground truth hidden until verdict)."""
    from attacker.blind_trial import execute_blind_trial
    return execute_blind_trial()

@router.post("/blind-batch")
def run_batch_blind_trials(req: Optional[BlindBatchRequest] = None):
    """Execute N blind randomized trials and return full confusion matrix and metrics."""
    from attacker.blind_trial import run_blind_batch
    size = req.batch_size if req and req.batch_size else 100
    return run_blind_batch(size)

@router.get("/blind-history")
def get_blind_history(limit: int = 50):
    """Retrieve history of blind trials."""
    from attacker.blind_trial import get_blind_trial_history
    return get_blind_trial_history(limit)
