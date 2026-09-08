"""
Q-SENTINEL Blind Trial Engine — Autonomous, Ground-Truth Blind Evaluation.

Generates randomized legitimate transmissions and 7 threat vectors with
dynamic parameters. The payload sent to /v1/qds/verify is identical in
schema and contains ZERO labels, scenario hints, or target layers.

Only AFTER the verification engine returns its independent verdict is the
ground truth revealed side-by-side for confusion matrix computation.
"""
import uuid
import time
import random
import copy
import requests
from typing import Dict, Any, Optional, List, Tuple

from attacker.client import get_base_payload, send_verify
from attacker.config import API_URL
from src.keyvault import global_keyvault
from src.keyvault.session_store import global_session_store
from src.qds.teleportation_qds import TeleportationQDS
from src.security.envelope import PQCEnvelope

TRIAL_TYPES = [
    "honest",
    "impersonation",
    "unauthorized_verifier",
    "replay",
    "double_consumption",
    "channel_noise",
    "signature_forgery",
    "quantum_forgery",
]

# Running in-memory trial accumulator
_BLIND_TRIAL_HISTORY: List[Dict[str, Any]] = []


def generate_blind_trial_payload(trial_type: Optional[str] = None) -> Tuple[dict, dict]:
    """
    Construct an HTTP verification payload and a strictly separated ground-truth record.
    The payload contains ONLY standard protocol fields:
      session_id, signer_id, verifier_id, nonce, timestamp, message_bit, revealed_keys, signature.
    """
    if not trial_type:
        trial_type = random.choice(TRIAL_TYPES)

    trial_id = f"trial-{uuid.uuid4()}"
    L = 100
    msg_bit = random.choice([0, 1])

    if trial_type == "honest":
        # Honest transmission: legitimate Alice, clean channel or tiny benign noise below tau_low (0.05)
        dist = round(random.uniform(0.0, 0.03), 3)
        payload = get_base_payload(
            signer_id="alice",
            verifier_id="bob",
            L=L,
            disturbance=dist,
            message_bit=msg_bit,
            experiment_id=trial_id
        )
        ground_truth = {
            "trial_id": trial_id,
            "type": "honest",
            "category": "HONEST",
            "expected_verdict": "ACCEPT",
            "expected_layer": "None (Pass)",
            "parameters": {"disturbance": dist, "signer": "alice", "verifier": "bob"}
        }
        return payload, ground_truth

    elif trial_type == "impersonation":
        # Adversary attempts to hijack Alice's session or forge Alice's signature
        adversary = random.choice(["eve", "mallory", "oscar", "trudy", "sybil_attacker"])
        payload = get_base_payload(
            signer_id="alice",
            verifier_id="bob",
            L=L,
            message_bit=msg_bit,
            experiment_id=trial_id
        )
        if adversary == "mallory":
            # Mallory signs Alice's session using Mallory's own key
            with open("attacker/credentials/mallory_sk.bin", "rb") as f:
                msk = f.read()
            payload["signature"] = PQCEnvelope.sign_payload(msk, payload)
        else:
            # Adversary claims session belonging to Alice
            payload["signer_id"] = adversary

        ground_truth = {
            "trial_id": trial_id,
            "type": "impersonation",
            "category": "ATTACK",
            "expected_verdict": "REJECT",
            "expected_layer": "L3 (AuthenticationProbe)",
            "parameters": {"adversary_signer": adversary}
        }
        return payload, ground_truth

    elif trial_type == "unauthorized_verifier":
        # Request sent to an unregistered or revoked verifier identity
        bad_verifier = random.choice(["unauthorized_node", "mallory_proxy", "revoked_node_4", "foreign_station"])
        payload = get_base_payload(
            signer_id="alice",
            verifier_id=bad_verifier,
            L=L,
            message_bit=msg_bit,
            experiment_id=trial_id
        )
        ground_truth = {
            "trial_id": trial_id,
            "type": "unauthorized_verifier",
            "category": "ATTACK",
            "expected_verdict": "REJECT",
            "expected_layer": "L3 (AuthorizationGuard)",
            "parameters": {"unauthorized_verifier": bad_verifier}
        }
        return payload, ground_truth

    elif trial_type == "channel_noise":
        # Controlled disturbance in transmission. Includes borderline values (e.g. 0.04 - 0.25)
        # Note: disturbance < 0.05 will ACCEPT (benign channel noise),
        # 0.05 - 0.15 will QUARANTINE, > 0.15 will REJECT.
        dist = round(random.uniform(0.04, 0.35), 3)
        expected_verdict = "ACCEPT" if dist < 0.05 else ("QUARANTINE" if dist <= 0.15 else "REJECT")
        payload = get_base_payload(
            signer_id="alice",
            verifier_id="bob",
            L=L,
            disturbance=dist,
            message_bit=msg_bit,
            experiment_id=trial_id
        )
        ground_truth = {
            "trial_id": trial_id,
            "type": "channel_noise",
            "category": "ATTACK" if dist >= 0.05 else "BORDERLINE_BENIGN",
            "expected_verdict": expected_verdict,
            "expected_layer": "L2 (StatisticalProbe / Tomography)",
            "parameters": {"disturbance": dist}
        }
        return payload, ground_truth

    elif trial_type == "signature_forgery":
        # Mutates classical signature payload after generation
        payload = get_base_payload(
            signer_id="alice",
            verifier_id="bob",
            L=L,
            message_bit=msg_bit,
            tamper_signature=True,
            experiment_id=trial_id
        )
        ground_truth = {
            "trial_id": trial_id,
            "type": "signature_forgery",
            "category": "ATTACK",
            "expected_verdict": "REJECT",
            "expected_layer": "L3 (PQCEnvelope / AuthenticationProbe)",
            "parameters": {"mutated_signature": True}
        }
        return payload, ground_truth

    elif trial_type == "quantum_forgery":
        # Mallory signs with valid ML-DSA-65 envelope but blind-guesses quantum bit allocations
        # Equivalent to maximum basis guessing noise (p ~ 0.25 on mismatched bases)
        payload = get_base_payload(
            signer_id="alice",
            verifier_id="bob",
            L=L,
            disturbance=0.25,
            message_bit=msg_bit,
            experiment_id=trial_id
        )
        ground_truth = {
            "trial_id": trial_id,
            "type": "quantum_forgery",
            "category": "ATTACK",
            "expected_verdict": "REJECT",
            "expected_layer": "L2 (StatisticalProbe)",
            "parameters": {"quantum_guessing_noise": 0.25}
        }
        return payload, ground_truth

    elif trial_type == "replay":
        # Executes legitimate setup request first, then replays identical payload
        original_payload = get_base_payload(
            signer_id="alice",
            verifier_id="bob",
            L=L,
            message_bit=msg_bit,
            experiment_id=f"setup-{trial_id}"
        )
        send_verify(original_payload)  # Consume nonce & session once
        replayed_payload = copy.deepcopy(original_payload)
        ground_truth = {
            "trial_id": trial_id,
            "type": "replay",
            "category": "ATTACK",
            "expected_verdict": "REJECT",
            "expected_layer": "L3 (FreshnessProbe / NonceGuard)",
            "parameters": {"replayed_nonce": original_payload["nonce"]}
        }
        return replayed_payload, ground_truth

    elif trial_type == "double_consumption":
        # Submits valid session once, then resubmits with NEW nonce but SAME session_id to same verifier
        original_payload = get_base_payload(
            signer_id="alice",
            verifier_id="bob",
            L=L,
            message_bit=msg_bit,
            experiment_id=f"setup-dc-{trial_id}"
        )
        send_verify(original_payload)  # Consume session
        # Construct fresh request for the same consumed session
        second_payload = copy.deepcopy(original_payload)
        second_payload["nonce"] = f"nonce-{uuid.uuid4()}"
        second_payload["timestamp"] = time.time()
        # Re-sign with updated nonce and timestamp
        with open("attacker/credentials/alice_sk.bin", "rb") as f:
            sk = f.read()
        second_payload["signature"] = PQCEnvelope.sign_payload(sk, second_payload)
        ground_truth = {
            "trial_id": trial_id,
            "type": "double_consumption",
            "category": "ATTACK",
            "expected_verdict": "REJECT",
            "expected_layer": "L3 (DoubleConsumptionGuard)",
            "parameters": {"reused_session": original_payload["session_id"]}
        }
        return second_payload, ground_truth

    else:
        raise ValueError(f"Unknown trial type: {trial_type}")


def execute_blind_trial(trial_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute a single blind trial:
    1. Privately construct payload and ground truth.
    2. Send payload to API (/v1/qds/verify) without any trial labels.
    3. Compare detector's unassisted verdict against ground truth.
    4. Return full forensic record.
    """
    payload, ground_truth = generate_blind_trial_payload(trial_type)

    raw = send_verify(payload)
    resp = raw.get("response", {})
    http_status = raw.get("http_status")
    
    # In Q-SENTINEL: L3 identity rejection returns 403; other decisions return 200 with JSON decision
    if http_status == 403:
        actual_decision = "REJECT"
        findings = [{"detector": "L3 Guard", "description": resp.get("detail", "Access Denied")}]
    else:
        actual_decision = resp.get("decision", "ERROR")
        findings = resp.get("findings", [])

    # Deduce primary detecting layer from live findings object
    detected_layers = set()
    for f in findings:
        det = f.get("detector", "") or f.get("detector_name", "")
        if any(w in det for w in ["Authentication", "Identity", "PQCEnvelope", "Freshness", "Nonce", "DoubleConsumption", "L3"]):
            detected_layers.add("L3")
        elif any(w in det for w in ["Statistical", "Tomography", "Quantum", "L2"]):
            detected_layers.add("L2")
        elif any(w in det for w in ["Ledger", "HMAC", "L4"]):
            detected_layers.add("L4")
        elif any(w in det for w in ["L1"]):
            detected_layers.add("L1")

    primary_layer = "/".join(sorted(detected_layers)) if detected_layers else "None"

    # Evaluation against Ground Truth:
    is_honest = ground_truth["type"] == "honest" or ground_truth["category"] == "BORDERLINE_BENIGN"
    
    if is_honest:
        correct = actual_decision == "ACCEPT"
        confusion_class = "TN" if correct else "FP"  # TN = honest correctly accepted; FP = false alarm
    else:
        correct = actual_decision in ["REJECT", "QUARANTINE"]
        confusion_class = "TP" if correct else "FN"  # TP = attack caught; FN = attack missed (false negative)

    trial_result = {
        "trial_id": ground_truth["trial_id"],
        "timestamp": time.time(),
        "ground_truth": {
            "type": ground_truth["type"],
            "category": ground_truth["category"],
            "expected_verdict": ground_truth["expected_verdict"],
            "expected_layer": ground_truth["expected_layer"],
            "parameters": ground_truth["parameters"],
        },
        "detector_result": {
            "actual_decision": actual_decision,
            "detected": actual_decision != "ACCEPT",
            "primary_layer": primary_layer,
            "findings_count": len(findings),
            "findings_sample": findings[:2] if findings else [],
            "latency_ms": resp.get("latency_ms", 0.0),
            "evidence_id": resp.get("evidence_id"),
        },
        "evaluation": {
            "correct": correct,
            "confusion_class": confusion_class,
            "match": actual_decision == ground_truth["expected_verdict"]
        }
    }

    _BLIND_TRIAL_HISTORY.append(trial_result)
    return trial_result


def run_blind_batch(count: int = 100) -> Dict[str, Any]:
    """
    Execute a batch of blind trials with uniform distribution across all types.
    Computes confusion matrix, precision, recall, and per-type statistics.
    """
    batch_results = []
    matrix = {"TP": 0, "TN": 0, "FP": 0, "FN": 0}
    type_stats: Dict[str, Dict[str, int]] = {}

    for t in TRIAL_TYPES:
        type_stats[t] = {"total": 0, "ACCEPT": 0, "QUARANTINE": 0, "REJECT": 0, "correct": 0}

    for i in range(count):
        chosen_type = TRIAL_TYPES[i % len(TRIAL_TYPES)]
        res = execute_blind_trial(chosen_type)
        batch_results.append(res)
        
        c_class = res["evaluation"]["confusion_class"]
        matrix[c_class] = matrix.get(c_class, 0) + 1

        t_type = res["ground_truth"]["type"]
        dec = res["detector_result"]["actual_decision"]
        type_stats[t_type]["total"] += 1
        type_stats[t_type][dec] = type_stats[t_type].get(dec, 0) + 1
        if res["evaluation"]["correct"]:
            type_stats[t_type]["correct"] += 1

    tp = matrix["TP"]
    tn = matrix["TN"]
    fp = matrix["FP"]
    fn = matrix["FN"]

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 1.0
    accuracy = (tp + tn) / count if count > 0 else 1.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "batch_size": count,
        "confusion_matrix": matrix,
        "metrics": {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "specificity": round(specificity, 4),
            "f1_score": round(f1, 4),
        },
        "type_breakdown": type_stats,
        "recent_trials": batch_results[-15:]
    }


def get_blind_trial_history(limit: int = 50) -> List[Dict[str, Any]]:
    return _BLIND_TRIAL_HISTORY[-limit:]
