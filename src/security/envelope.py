"""
Q-SENTINEL PQC Envelope.

Implements ML-DSA-65 (FIPS 204) for post-quantum classical authentication
of verification requests. Replaces the name-based allowlists.
"""
from pqcrypto.sign import ml_dsa_65
import base64
import json

class PQCEnvelope:
    
    @staticmethod
    def generate_keypair() -> tuple[bytes, bytes]:
        """Generate an ML-DSA-65 keypair. Returns (pk, sk)."""
        return ml_dsa_65.keygen()
        
    @staticmethod
    def sign_payload(sk: bytes, payload_dict: dict) -> str:
        """
        Sign a canonicalized JSON payload.
        Returns the signature as a base64 string.
        """
        # Canonical JSON string (sorted keys, no spaces)
        message = json.dumps(payload_dict, sort_keys=True, separators=(',', ':')).encode('utf-8')
        sig = ml_dsa_65.sign(sk, message)
        return base64.b64encode(sig).decode('utf-8')
        
    @staticmethod
    def verify_payload(pk: bytes, payload_dict: dict, signature_b64: str) -> bool:
        """
        Verify a signature against a payload dict.
        """
        try:
            message = json.dumps(payload_dict, sort_keys=True, separators=(',', ':')).encode('utf-8')
            sig = base64.b64decode(signature_b64)
            ml_dsa_65.verify(pk, message, sig)
            return True
        except Exception:
            return False

