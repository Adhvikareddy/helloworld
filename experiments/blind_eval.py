"""
Q-SENTINEL Blind Evaluation.

Runs a predeclared population of legitimate and adversarial verification
requests against the API. Computes standard detection metrics.
"""
import uuid
import time
from src.transport.client import TransportClient
from attacker.scenarios import AttackerHarness

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

    # Phase 1: Legitimate requests
    print(f"[1/2] Running {n_legitimate} legitimate requests...")
    for i in range(n_legitimate):
        session = global_keyvault.create_session("alice", 300)
        payload, _ = harness.replay_attack() # This returns a valid base payload
        payload["session_id"] = session.session_id
        
        # Re-sign with correct session_id
        from src.security.envelope import PQCEnvelope
        with open("attacker/credentials/alice_sk.bin", "rb") as f:
            alice_sk = f.read()
            
        payload["signature"] = PQCEnvelope.sign_payload(alice_sk, payload)
        
        resp = client.post_verification(payload)
        
        if resp.status_code == 200:
            decision = resp.json().get("decision", "ERROR")
            if decision == "ACCEPT":
                TP += 1
            else:
                FN += 1
        else:
            FN += 1

    # Phase 2: Adversarial requests (valid-path forgery)
    print(f"[2/2] Running {n_adversarial} adversarial requests (disturbance={adversarial_disturbance})...")
    for i in range(n_adversarial):
        session = global_keyvault.create_session("alice", 300)
        payload, _ = harness.replay_attack() 
        payload["session_id"] = session.session_id
        payload["signature"] = PQCEnvelope.sign_payload(alice_sk, payload)
        
        headers = {"x-testbed-disturbance": str(adversarial_disturbance)}
        
        resp = client.post_verification(payload, headers=headers)
        
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
