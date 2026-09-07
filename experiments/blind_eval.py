import time
from attacker.client import run_attack

def run_blind_evaluation():
    print("Starting blind evaluation...")
    TP = 0
    TN = 0
    FP = 0
    FN = 0
    
    forgery_accepted = 0
    total_forgeries = 20
    total_legitimate = 20
    
    print(f"Running {total_legitimate} legitimate requests...")
    for _ in range(total_legitimate):
        code, res = run_attack("legitimate")
        if res.get("decision") == "ACCEPT":
            TP += 1
        else:
            FN += 1
            
    print(f"Running {total_forgeries} valid-path forgery attempts...")
    for _ in range(total_forgeries):
        def mod(p):
            p["experiment_id"] = "forgery_b"
            # Introduce a disturbance to simulate a valid-path forgery attack modifying state
            p["disturbance_prob"] = 0.25 
            return p
        code, res = run_attack("forgery_b", mod)
        if res.get("decision") == "ACCEPT":
            FP += 1
            forgery_accepted += 1
        else:
            TN += 1
            
    total_adv = total_forgeries
    
    FAR = FP / (FP + TN) if (FP + TN) > 0 else 0.0
    FRR = FN / (TP + FN) if (TP + FN) > 0 else 0.0
    accuracy = (TP + TN) / (total_legitimate + total_adv) if (total_legitimate + total_adv) > 0 else 0.0
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    p_forge = forgery_accepted / total_forgeries if total_forgeries > 0 else 0.0
    
    metrics = {
        "TP": TP, "TN": TN, "FP": FP, "FN": FN,
        "FAR": FAR, "FRR": FRR, "Accuracy": accuracy,
        "Precision": precision, "Recall": recall, "F1": f1,
        "Empirical Forgery Acceptance": p_forge
    }
    
    print("\n--- Blind Evaluation Results ---")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    run_blind_evaluation()
