"""
Q-SENTINEL PQC Identity and Authorization.

Uses ML-DSA-65 public keys instead of names to identify and authorize participants.
"""
from src.security.envelope import PQCEnvelope

class PQCIdentityManager:
    """Manages public keys of authorized participants."""
    
    def __init__(self):
        self.registered_pks = {}
        self.authorized_verifiers = set()
        
    def register_participant(self, name: str, pk: bytes, is_verifier: bool = False):
        """Register a participant's public key."""
        self.registered_pks[name] = pk
        if is_verifier:
            self.authorized_verifiers.add(name)
            
    def get_public_key(self, name: str) -> bytes:
        return self.registered_pks.get(name)
        
    def is_verifier_authorized(self, name: str) -> bool:
        return name in self.authorized_verifiers
        
    def verify_request_signature(self, signer_id: str, payload_dict: dict, signature_b64: str) -> bool:
        """Verify that the request is signed by the claimed signer."""
        pk = self.get_public_key(signer_id)
        if not pk:
            return False
        return PQCEnvelope.verify_payload(pk, payload_dict, signature_b64)

# Global instance for the API
global_pqc_identity = PQCIdentityManager()
