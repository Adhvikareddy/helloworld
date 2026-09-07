class AuthorizationGuard:
    """
    Validates that the verifier is authorized to process the verification request.
    """
    @staticmethod
    def is_authorized(verifier_id: str) -> bool:
        # In a full implementation, this checks an authorization policy or RBAC system.
        # For the hackathon testbed, we simulate unauthorized verifier attacks by 
        # rejecting known adversarial verifiers.
        if verifier_id == "unauthorized_verifier" or verifier_id == "eve":
            return False
        return True
