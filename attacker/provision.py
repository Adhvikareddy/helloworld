"""
Q-SENTINEL Credential Provisioning.

Generates and saves ML-DSA-65 keypairs for the testbed participants:
Alice (signer), Bob (verifier 1), Charlie (verifier 2), Mallory (attacker).
"""
import os
import json
from src.security.envelope import PQCEnvelope
import base64

def provision_credentials(out_dir: str = "attacker/credentials"):
    os.makedirs(out_dir, exist_ok=True)
    
    participants = ["alice", "bob", "charlie", "mallory"]
    registry = {}
    
    for p in participants:
        print(f"Provisioning {p}...")
        pk, sk = PQCEnvelope.generate_keypair()
        
        # Save private key to individual file
        with open(os.path.join(out_dir, f"{p}_sk.bin"), "wb") as f:
            f.write(sk)
            
        # Add to public registry
        registry[p] = base64.b64encode(pk).decode('utf-8')
        
    with open(os.path.join(out_dir, "public_registry.json"), "w") as f:
        json.dump(registry, f, indent=2)
        
    print("Provisioning complete.")

if __name__ == "__main__":
    provision_credentials()
