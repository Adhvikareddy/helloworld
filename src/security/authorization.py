class AuthorizationGuard:
    """
    Validates that the verifier is authorized to process the verification request.

    Testbed implementation:
      Uses an allowlist of authorized verifiers.  Any verifier_id NOT in the
      authorized set is rejected.  In a production system this would check
      an authorization policy, RBAC system, or verifier certificate.
    """

    # Authorized verifiers in the testbed — extend as needed
    AUTHORIZED_VERIFIERS = {"bob", "alice", "charlie", "david"}

    @staticmethod
    def is_authorized(verifier_id: str) -> bool:
        """Return True only if the verifier is authorized."""
        return verifier_id in AuthorizationGuard.AUTHORIZED_VERIFIERS
