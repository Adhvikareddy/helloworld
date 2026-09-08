"""
Q-SENTINEL Key Vault.

Manages generation, storage, and reveal of single-use quantum key sets.
Enforces the single-use property to prevent key reuse attacks.
"""
import uuid
import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from src.qds.key_material import QuantumKeyElement, generate_key_set


@dataclass
class KeySession:
    """A session binding a signer to a set of pre-distributed keys."""
    session_id: str
    signer_id: str
    L: int
    k_0: List[QuantumKeyElement]
    k_1: List[QuantumKeyElement]
    created_at: float = field(default_factory=time.time)
    used: bool = False


class KeyVault:
    """
    In-memory key vault for demonstrating the protocol.
    In a real implementation, this would be a secure enclave or HSM.
    """
    
    def __init__(self):
        self._sessions: Dict[str, KeySession] = {}
        # Track used session IDs globally to prevent reuse across restarts if backed by DB
        self._used_sessions: Set[str] = set()

    def create_session(self, signer_id: str, L: int) -> KeySession:
        """
        Create a new key distribution session for a signer.
        Generates fresh key material.
        """
        session_id = f"session-{uuid.uuid4()}"
        k_0, k_1 = generate_key_set(L)
        
        session = KeySession(
            session_id=session_id,
            signer_id=signer_id,
            L=L,
            k_0=k_0,
            k_1=k_1
        )
        self._sessions[session_id] = session
        return session

    def get_session_for_distribution(self, session_id: str) -> Optional[KeySession]:
        """
        Retrieve a session for the distribution phase.
        Does NOT mark it as used yet, because distribution happens before signing.
        """
        return self._sessions.get(session_id)

    def reveal_keys(self, session_id: str, signer_id: str, message_bit: int) -> List[QuantumKeyElement]:
        """
        Reveal the classical key material for a specific message bit.
        This represents Alice sending the classical description of her states to Bob.
        
        CRITICAL: This marks the session as used. It cannot be used again.
        """
        if session_id in self._used_sessions:
            raise ValueError(f"Session {session_id} has already been used.")
            
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found.")
            
        if session.signer_id != signer_id:
            raise ValueError(f"Signer {signer_id} is not authorized for session {session_id}.")
            
        if message_bit not in (0, 1):
            raise ValueError(f"Message bit must be 0 or 1, got {message_bit}.")
            
        # Mark as used immediately before returning keys
        session.used = True
        self._used_sessions.add(session_id)
        
        if message_bit == 0:
            return session.k_0
        else:
            return session.k_1
            
# Global instance for the API to use
global_keyvault = KeyVault()
