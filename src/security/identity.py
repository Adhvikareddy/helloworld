class IdentityGuard:
    """
    Validates that the signer identity is bound to the current session/key context.

    Testbed implementation:
      Uses an allowlist of registered signers.  Any signer_id NOT in the
      registered set is rejected.  In a production system this would verify
      a cryptographic certificate binding between signer_id and session.
    """

    # Registered signers in the testbed — extend as needed
    REGISTERED_SIGNERS = {"alice", "bob", "charlie", "david"}

    @staticmethod
    def verify_binding(signer_id: str, session_id: str) -> bool:
        """Return True only if the signer is a registered identity."""
        return signer_id in IdentityGuard.REGISTERED_SIGNERS
