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
        return {
            "session_id": f"session-{uuid.uuid4()}",
            "signer_id": "alice",
            "verifier_id": "bob",
            "nonce": f"nonce-{uuid.uuid4()}",
            "timestamp": time.time(),
            "message_bit": 0,
            "measurement_bases": ["X", "Y", "Z"] * 100, # L=300
            "experiment_id": "test_run"
        }

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
    def quantum_forgery(self) -> tuple[Dict[str, Any], dict]:
        """
        Mallory guesses the quantum states.
        Because we can't actually intercept the simulated channel easily from the HTTP client,
        we simulate this by providing completely random measurement bases that don't match the key.
        Actually, the simulator will run the circuits, but we can't easily force it to use Mallory's guesses
        without modifying the API just for the test.
        
        Instead, we will rely on the unit/integration tests to directly call `compute_mismatch_rate`
        with simulated adversarial guesses to prove the bounds.
        """
        payload = self._build_base_payload()
        sig = PQCEnvelope.sign_payload(self.alice_sk, payload)
        payload["signature"] = sig
        return payload, {"x_testbed_disturbance": 1.0} # Force max error to simulate totally wrong states

    # 5. Channel Manipulation (L2 Statistical)
    def channel_manipulation(self, disturbance: float = 0.5) -> tuple[Dict[str, Any], dict]:
        """Mallory injects noise into the quantum channel."""
        payload = self._build_base_payload()
        sig = PQCEnvelope.sign_payload(self.alice_sk, payload)
        payload["signature"] = sig
        return payload, {"x_testbed_disturbance": disturbance}

    # 6. Replay Attack (L3 Freshness)
    def replay_attack(self) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Return the same valid payload twice."""
        payload = self._build_base_payload()
        sig = PQCEnvelope.sign_payload(self.alice_sk, payload)
        payload["signature"] = sig
        return payload, payload # Return it twice to send sequentially

    # 7. Composite Attack (Multiple vectors simultaneously)
    def composite_attack(self) -> tuple[Dict[str, Any], dict]:
        """Impersonation + Stale Timestamp + Forged Quantum."""
        payload = self._build_base_payload()
        payload["timestamp"] = time.time() - 3600 # Stale
        payload["signer_id"] = "alice"
        
        # Signed by Mallory
        sig = PQCEnvelope.sign_payload(self.mallory_sk, payload)
        payload["signature"] = sig
        
        return payload, {"x_testbed_disturbance": 1.0}

