"""
Unauthorized Verification Attack — L3 authorization policy test.

The attacker submits verification requests using verifier identities that
are NOT authorized.  L3 must reject BEFORE quantum/statistical processing.
"""
import uuid
import datetime
from attacker.client import get_base_payload, send_verify
from attacker.reporting import make_attack_result, print_result, aggregate_results
from attacker.config import DEFAULT_REPEAT_COUNT

UNAUTHORIZED_VERIFIERS = [
    "unauthorized_verifier", "eve", "unregistered_node",
    "revoked_verifier", "external_agent",
]


def run_unauthorized(count: int = DEFAULT_REPEAT_COUNT) -> list:
    """
    Execute unauthorized verification attempts.

    For each attempt:
      1. Construct a valid verification request.
      2. Replace verifier_id with an unauthorized identity.
      3. Submit via normal API.
      4. Verify L3 REJECT with reason=authorization failure.
    """
    results = []
    run_id = f"unauthorized-{uuid.uuid4()}"

    for i in range(count):
        started = datetime.datetime.utcnow().isoformat()
        bad_verifier = UNAUTHORIZED_VERIFIERS[i % len(UNAUTHORIZED_VERIFIERS)]
        payload = get_base_payload(
            verifier_id=bad_verifier,
            experiment_id=f"unauthorized_{i}",
        )

        raw = send_verify(payload)
        resp = raw["response"]
        actual_decision = "REJECT" if raw["http_status"] == 403 else resp.get("decision", "ERROR")
        reason = resp.get("detail", resp.get("reason", ""))

        results.append(make_attack_result(
            attack_type="unauthorized_verification",
            target="/v1/qds/verify",
            expected_primary_layer="L3",
            expected_outcome="REJECT",
            actual_outcome=actual_decision,
            detected=actual_decision != "ACCEPT",
            event_id=resp.get("evidence_id"),
            reason=reason,
            parameters={"unauthorized_verifier_id": bad_verifier, "attempt": i},
            error=raw["error"],
            run_id=run_id,
            started_at=started,
            completed_at=raw["completed_at"],
        ))

    return results


if __name__ == "__main__":
    results = run_unauthorized()
    for r in results:
        print_result(r)
    print("\nAggregate:", aggregate_results(results))
