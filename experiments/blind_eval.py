"""
Q-SENTINEL Blind Evaluation.

Runs a predeclared population of legitimate and adversarial verification
requests against the API. Computes standard detection metrics.
"""
import uuid
import time
from src.transport.client import TransportClient
from attacker.harness import AttackerHarness

def run_blind_evaluation(
    n_legitimate: int = 20,
    n_adversarial: int = 20,
    adversarial_disturbance: float = 0.25,
):
    print("=" * 60)
    print("  Q-SENTINEL Blind Evaluation")
    print("=" * 60)
    print(f"  Legitimate: {n_legitimate}")
    print(f"  Adversarial: {n_adversarial} (disturbance={adversarial_disturbance})")
    print()

    client = TransportClient("http://localhost:8000")
    harness = AttackerHarness()

    TP = 0  # legitimate correctly ACCEPTED
    FN = 0  # legitimate incorrectly NOT accepted
    TN = 0  # adversarial correctly NOT accepted
    FP = 0  # adversarial incorrectly ACCEPTED
    
    # We need a fresh session for each request so L1 and L3 pass cleanly
    # For a real integration we'd call the keyvault API or use mock.
    # Here we'll just inject sessions into the global keyvault
    from src.keyvault import global_keyvault

    import random
    from src.qds.teleportation_qds import TeleportationQDS
    from src.security.envelope import PQCEnvelope
    from src.keyvault.session_store import global_session_store

    with open("attacker/credentials/alice_sk.bin", "rb") as f:
        alice_sk = f.read()

    # Phase 1: Legitimate requests
    print(f"[1/2] Running {n_legitimate} legitimate requests...")
    qds_clean = TeleportationQDS(disturbance_prob=0.0)
    for i in range(n_legitimate):
        session = global_keyvault.create_session("alice", 300)
        
        # Teleportation over clean channel (disturbance=0.0)
        rng = random.Random(f"{session.session_id}:bob")
        bob_bases = [rng.choice(["X", "Z"]) for _ in range(300)]
        bob_outcomes, _ = qds_clean.execute_session(
            session.k_0, bob_bases, f"{session.session_id}:bob", disturbance=0.0
        )
        global_session_store.store_verifier_outcomes(
            session.session_id, "bob", bob_bases, bob_outcomes
        )
        
        payload, _ = harness.replay_attack()
        payload["session_id"] = session.session_id
        payload["revealed_keys"] = [{"bit_index": idx, "basis": k.basis, "bit_value": k.bit} for idx, k in enumerate(session.k_0)]
        payload.pop("signature", None)
        payload["signature"] = PQCEnvelope.sign_payload(alice_sk, payload)
        
        resp = client.post_verification(payload)
        
        if resp.status_code == 200:
            decision = resp.json().get("decision", "ERROR")
            if decision == "ACCEPT":
                TP += 1
            else:
                print(f"Legitimate failed: {resp.json()}")
                FN += 1
        else:
            print(f"Legitimate failed status {resp.status_code}: {resp.text}")
            FN += 1

    # Phase 2: Adversarial requests (valid-path forgery under channel disturbance)
    print(f"[2/2] Running {n_adversarial} adversarial requests (disturbance={adversarial_disturbance})...")
    qds_noisy = TeleportationQDS(disturbance_prob=adversarial_disturbance)
    for i in range(n_adversarial):
        session = global_keyvault.create_session("alice", 300)
        rng = random.Random(f"{session.session_id}:bob:{i}")
        bob_bases = [rng.choice(["X", "Z"]) for _ in range(300)]
        bob_outcomes, _ = qds_noisy.execute_session(
            session.k_0, bob_bases, f"{session.session_id}:bob:{i}", disturbance=adversarial_disturbance
        )
        global_session_store.store_verifier_outcomes(
            session.session_id, "bob", bob_bases, bob_outcomes
        )
        
        payload, _ = harness.replay_attack()
        payload["session_id"] = session.session_id
        payload["revealed_keys"] = [{"bit_index": idx, "basis": k.basis, "bit_value": k.bit} for idx, k in enumerate(session.k_0)]
        payload.pop("signature", None)
        payload["signature"] = PQCEnvelope.sign_payload(alice_sk, payload)
        
        resp = client.post_verification(payload)
        
        if resp.status_code == 200:
            decision = resp.json().get("decision", "ERROR")
            if decision == "ACCEPT":
                FP += 1
            else:
                TN += 1
        else:
            TN += 1

    # Compute metrics
    total = n_legitimate + n_adversarial
    accuracy = (TP + TN) / total if total > 0 else 0.0
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    FAR = FP / (FP + TN) if (FP + TN) > 0 else 0.0
    FRR = FN / (TP + FN) if (TP + FN) > 0 else 0.0
    P_forge = FP / n_adversarial if n_adversarial > 0 else 0.0

    metrics = {
        "TP": TP,
        "TN": TN,
        "FP": FP,
        "FN": FN,
        "Accuracy": round(accuracy, 4),
        "Precision": round(precision, 4),
        "Recall": round(recall, 4),
        "F1": round(f1, 4),
        "FAR (False Accept Rate)": round(FAR, 4),
        "FRR (False Reject Rate)": round(FRR, 4),
        "P_forge_emp": round(P_forge, 4),
    }

    print()
    print("=" * 60)
    print("  Blind Evaluation Results")
    print("=" * 60)
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    print()
    print("=" * 60)

    return metrics

if __name__ == "__main__":
    # Ensure API is up before running
    run_blind_evaluation()
