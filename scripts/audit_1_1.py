import sys
import os
import random

# Add parent directory to path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.qds.teleportation_qds import TeleportationQDS
from src.qds.key_material import QuantumKeyElement
from src.qds.verification import compute_mismatch_rate

def run_experiment():
    disturbances = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5]
    num_elements = 500
    
    print("Disturbance | Mismatch Rate | Mismatches / Matches")
    print("-" * 55)
    
    for dist in disturbances:
        # Create random keys and bases for Bob
        alice_keys = []
        bob_bases = []
        bases = ["X", "Y", "Z"]
        
        for _ in range(num_elements):
            b = random.choice(bases)
            bit = random.choice([0, 1])
            alice_keys.append(QuantumKeyElement(basis=b, bit=bit))
            bob_bases.append(random.choice(bases))
            
        qds = TeleportationQDS(disturbance_prob=dist, seed=42)
        # Note: execute_session expects pure_x_rotation to be set if we want disturbance to manifest as X rotation?
        # Let's check TeleportationQDS: "pure_x_rotation and disturbance > 0.0: qc.rx(...)".
        # But wait, TeleportationQDS also says: "self.noise_model = get_noise_model(disturbance_prob)"
        # So maybe disturbance applies via noise_model even if pure_x_rotation=False?
        # Let's run it both ways or just as the API does.
        # The prompt mentions "for each value of disturbance_prob... run execute_session".
        bob_outcomes, metadata = qds.execute_session(
            alice_keys=alice_keys,
            bob_bases=bob_bases,
            seed_material="test_seed_material_123",
            pure_x_rotation=False,
            disturbance=dist
        )
        
        mismatch_rate, mismatches, matches = compute_mismatch_rate(alice_keys, bob_bases, bob_outcomes)
        print(f"{dist:<11} | {mismatch_rate:<13.4f} | {mismatches} / {matches}")

if __name__ == "__main__":
    run_experiment()
