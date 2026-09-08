"""
Q-SENTINEL Attack Scenarios (F1 - F8).

Comprehensive test harness implementing the 7 specific attack vectors
outlined in the THREAT_MODEL.md plus composite/adaptive attacks.
"""
import uuid
import time
import json
import base64
from typing import Dict, Any, List
from src.security.envelope import PQCEnvelope

class AttackerHarness:
    def __init__(self, registry_path="attacker/credentials/public_registry.json"):
        with open(registry_path, "r") as f:
            self.registry = json.load(f)
            
        # Load Mallory's private key
        with open("attacker/credentials/mallory_sk.bin", "rb") as f:
            self.mallory_sk = f.read()
            
        # We need Alice's SK for legitimate testing, but Mallory doesn't have it
        with open("attacker/credentials/alice_sk.bin", "rb") as f:
            self.alice_sk = f.read()

    def _build_base_payload(self) -> Dict[str, Any]:
        from attacker.client import get_base_payload
        return get_base_payload(signer_id="alice", verifier_id="bob", disturbance=0.0)

    # 1. Impersonation (L3 - Authentication)
    def impersonate_alice(self) -> Dict[str, Any]:
        """Mallory attempts to sign as Alice using Mallory's own key."""
        payload = self._build_base_payload()
        payload["signer_id"] = "alice"
        
        # Mallory signs the payload (invalid because it won't match Alice's PK)
        sig = PQCEnvelope.sign_payload(self.mallory_sk, payload)
        payload["signature"] = sig
        return payload

    # 2. Unauthorized Verification (L3 - Authorization)
    def unauthorized_verifier(self) -> Dict[str, Any]:
        """Mallory attempts to invoke the verification endpoint."""
        payload = self._build_base_payload()
        payload["verifier_id"] = "mallory"
        
        # Alice legitimately signs it, but Mallory is not an authorized verifier
        sig = PQCEnvelope.sign_payload(self.alice_sk, payload)
        payload["signature"] = sig
        return payload

    # 3. Forgery A - Invalid Signature Path (L1 Core)
    def invalid_signature_path(self) -> Dict[str, Any]:
        """Submit a completely malformed signature string."""
        payload = self._build_base_payload()
        payload["signature"] = "invalid_base64_garbage!!!"
        return payload

    # 4. Forgery B - Quantum Forgery (L2 Statistical)
    def quantum_forgery(self) -> Dict[str, Any]:
        """Mallory holds a valid classical signature but guesses quantum states."""
        from attacker.client import get_base_payload
        return get_base_payload(mutate_keys=True, mutation_rate=0.35)

    # 5. Channel Manipulation (L2 Statistical)
    def channel_manipulation(self, disturbance: float = 0.5) -> Dict[str, Any]:
        """Channel perturbation scenario."""
        from attacker.client import get_base_payload
        return get_base_payload(disturbance=disturbance)

    # 6. Replay Attack (L3 Freshness)
    def replay_attack(self) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Return the same valid payload twice."""
        payload = self._build_base_payload()
        sig = PQCEnvelope.sign_payload(self.alice_sk, payload)
        payload["signature"] = sig
        return payload, payload # Return it twice to send sequentially

    # 7. Composite Attack (Multiple vectors simultaneously)
    def composite_attack(self) -> Dict[str, Any]:
        """Impersonation + Stale Timestamp + Forged Quantum."""
        payload = self._build_base_payload()
        payload["timestamp"] = time.time() - 3600 # Stale
        payload["signer_id"] = "alice"
        
        # Signed by Mallory
        sig = PQCEnvelope.sign_payload(self.mallory_sk, payload)
        payload["signature"] = sig
        return payload

