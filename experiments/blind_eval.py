"""
Q-SENTINEL Blind Evaluation (T6).

Runs a predeclared population of legitimate and adversarial verification requests.
Threat is strictly the positive class:
- True Positive (TP): Adversarial request (forgery / threat) correctly REJECTED.
- False Negative (FN): Adversarial request incorrectly ACCEPTED.
- True Negative (TN): Legitimate request correctly ACCEPTED.
- False Positive (FP): Legitimate request incorrectly REJECTED.

Writes results to experiments/results/blind_eval.csv with columns:
class,n,tp,fp,tn,fn,tpr,fpr,precision,recall,f1
"""
import os
import sys
import csv
import time
import uuid
import random

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from apps.api.main import app
from src.security.envelope import PQCEnvelope
from src.security.identity import global_pqc_identity
from src.keyvault.session_store import global_session_store


def run_blind_evaluation(
    n_legitimate: int = 25,
    n_adversarial: int = 25,
    out_path: str = "experiments/results/blind_eval.csv"
):
    print("=" * 60)
    print("  Q-SENTINEL Blind Evaluation (Threat = Positive Class)")
    print("=" * 60)
    print(f"  Legitimate (Negative): {n_legitimate}")
    print(f"  Adversarial (Positive): {n_adversarial}")

    client = TestClient(app)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    alice_pk, alice_sk = PQCEnvelope.generate_keypair()
    mallory_pk, mallory_sk = PQCEnvelope.generate_keypair()
    global_pqc_identity.register_participant("alice_eval", alice_pk, is_verifier=False, role="auditor")
    global_pqc_identity.register_participant("bob_eval", alice_pk, is_verifier=True, role="verifier")
    global_pqc_identity.register_participant("mallory_eval", mallory_pk, is_verifier=False, role="verifier")

    TP = 0  # Threat correctly rejected
    FN = 0  # Threat incorrectly accepted
    TN = 0  # Legitimate correctly accepted
    FP = 0  # Legitimate incorrectly rejected

    # Phase 1: Legitimate verification requests (Negative Class)
    print(f"[1/2] Evaluating {n_legitimate} legitimate requests...")
    for i in range(n_legitimate):
        session_id = f"sess-legit-{uuid.uuid4()}"
        L = 60
        dist_payload = {
            "session_id": session_id,
            "signer_id": "alice_eval",
            "verifiers": ["bob_eval"],
            "L": L,
            "nonce": f"nonce-dist-legit-{uuid.uuid4()}",
            "timestamp": time.time()
        }
        dist_payload["signature"] = PQCEnvelope.sign_payload(alice_sk, dist_payload)
        client.post("/v1/qds/distribute", json=dist_payload)

        rev_payload = {
            "session_id": session_id,
            "signer_id": "alice_eval",
            "message_bit": 0,
            "nonce": f"nonce-rev-legit-{uuid.uuid4()}",
            "timestamp": time.time()
        }
        rev_payload["signature"] = PQCEnvelope.sign_payload(alice_sk, rev_payload)
        rev_res = client.post("/v1/qds/reveal", json=rev_payload)
        revealed_keys = rev_res.json()["revealed_keys"]

        ver_payload = {
            "session_id": session_id,
            "signer_id": "alice_eval",
            "verifier_id": "bob_eval",
            "nonce": f"nonce-ver-legit-{uuid.uuid4()}",
            "timestamp": time.time(),
            "message_bit": 0,
            "revealed_keys": revealed_keys
        }
        ver_payload["signature"] = PQCEnvelope.sign_payload(alice_sk, ver_payload)
        res = client.post("/v1/qds/verify", json=ver_payload)

        decision = res.json().get("decision", "REJECT") if res.status_code == 200 else "REJECT"
        if decision == "ACCEPT":
            TN += 1
        else:
            FP += 1

    # Phase 2: Adversarial verification requests (Positive Class)
    print(f"[2/2] Evaluating {n_adversarial} adversarial requests...")
    for i in range(n_adversarial):
        session_id = f"sess-adv-{uuid.uuid4()}"
        L = 60
        dist_payload = {
            "session_id": session_id,
            "signer_id": "alice_eval",
            "verifiers": ["bob_eval"],
            "L": L,
            "nonce": f"nonce-dist-adv-{uuid.uuid4()}",
            "timestamp": time.time()
        }
        dist_payload["signature"] = PQCEnvelope.sign_payload(alice_sk, dist_payload)
        client.post("/v1/qds/distribute", json=dist_payload)

        attack_type = i % 4
        if attack_type == 0:
            # Vector 1: Uniformly random guessed quantum keys
            forged_keys = [
                {"bit_index": j, "basis": random.choice(["X", "Y", "Z"]), "bit_value": random.choice([0, 1])}
                for j in range(L)
            ]
            signer_key = alice_sk
            signer_id = "alice_eval"
            ts = time.time()
            nonce = f"nonce-adv-{uuid.uuid4()}"
        elif attack_type == 1:
            # Vector 2: Replay attack (reusing old nonce)
            v_data = global_session_store.get_verifier_outcomes(session_id, "bob_eval")
            bob_bases, bob_outcomes = v_data
            forged_keys = [{"bit_index": j, "basis": bob_bases[j], "bit_value": bob_outcomes[j]} for j in range(L)]
            signer_key = alice_sk
            signer_id = "alice_eval"
            ts = time.time()
            nonce = "static-replayed-nonce-12345"
            # prime the nonce first
            from src.security.nonce import global_nonce_guard
            global_nonce_guard.is_fresh(nonce, session_id)
        elif attack_type == 2:
            # Vector 3: Classical impersonation (Mallory signing for Alice)
            forged_keys = [{"bit_index": j, "basis": "X", "bit_value": 0} for j in range(L)]
            signer_key = mallory_sk
            signer_id = "alice_eval"
            ts = time.time()
            nonce = f"nonce-adv-{uuid.uuid4()}"
        else:
            # Vector 4: Stale timestamp / replay window expired
            forged_keys = [{"bit_index": j, "basis": "Z", "bit_value": 1} for j in range(L)]
            signer_key = alice_sk
            signer_id = "alice_eval"
            ts = time.time() - 3600.0
            nonce = f"nonce-adv-{uuid.uuid4()}"

        ver_payload = {
            "session_id": session_id,
            "signer_id": signer_id,
            "verifier_id": "bob_eval",
            "nonce": nonce,
            "timestamp": ts,
            "message_bit": 0,
            "revealed_keys": forged_keys
        }
        ver_payload["signature"] = PQCEnvelope.sign_payload(signer_key, ver_payload)
        res = client.post("/v1/qds/verify", json=ver_payload)

        decision = res.json().get("decision", "REJECT") if res.status_code == 200 else "REJECT"
        if decision in ["REJECT", "QUARANTINE"]:
            TP += 1
        else:
            FN += 1

    total_n = n_legitimate + n_adversarial
    tpr = TP / (TP + FN) if (TP + FN) > 0 else 0.0
    fpr = FP / (FP + TN) if (FP + TN) > 0 else 0.0
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
    recall = tpr
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    print(f"Results: TP={TP}, FP={FP}, TN={TN}, FN={FN}")
    print(f"TPR (Threat Recall)={tpr:.4f}, FPR (False Alarm Rate)={fpr:.4f}, Precision={precision:.4f}, F1={f1:.4f}")

    rows = [
        {
            "class": "threat",
            "n": n_adversarial,
            "tp": TP,
            "fp": FP,
            "tn": TN,
            "fn": FN,
            "tpr": f"{tpr:.4f}",
            "fpr": f"{fpr:.4f}",
            "precision": f"{precision:.4f}",
            "recall": f"{recall:.4f}",
            "f1": f"{f1:.4f}"
        },
        {
            "class": "overall",
            "n": total_n,
            "tp": TP,
            "fp": FP,
            "tn": TN,
            "fn": FN,
            "tpr": f"{tpr:.4f}",
            "fpr": f"{fpr:.4f}",
            "precision": f"{precision:.4f}",
            "recall": f"{recall:.4f}",
            "f1": f"{f1:.4f}"
        }
    ]

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["class", "n", "tp", "fp", "tn", "fn", "tpr", "fpr", "precision", "recall", "f1"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")
    return rows


if __name__ == "__main__":
    run_blind_evaluation()
