"""
Impersonation Attack — L3 identity-binding test.

The attacker constructs a request where the signer_id does NOT match
the expected session/key binding.  L3 must reject before the quantum
execution path is consumed.
"""
import uuid
import datetime
from attacker.client import get_base_payload, send_verify
from attacker.reporting import make_attack_result, print_result, aggregate_results
from attacker.config import DEFAULT_REPEAT_COUNT

# Identities that are known to be adversarial / not bound to any session
ADVERSARIAL_SIGNERS = ["impersonator", "eve", "mallory", "oscar", "trudy"]


def run_impersonation(count: int = DEFAULT_REPEAT_COUNT) -> list:
    """
    Execute impersonation attacks with genuinely inconsistent identity contexts.

    For each attempt:
      1. Construct a legitimate request payload (valid session, nonce, timestamp).
      2. Replace signer_id with an adversarial identity NOT bound to the session.
      3. Submit via normal API.
      4. Verify L3 REJECT with reason=identity-binding failure.
    """
    results = []
    run_id = f"impersonation-{uuid.uuid4()}"

    for i in range(count):
        started = datetime.datetime.utcnow().isoformat()
        adversary = ADVERSARIAL_SIGNERS[i % len(ADVERSARIAL_SIGNERS)]
        payload = get_base_payload(
            signer_id=adversary,
            experiment_id=f"impersonation_{i}",
        )

        raw = send_verify(payload)
        resp = raw["response"]
        actual_decision = "REJECT" if raw["http_status"] == 403 else resp.get("decision", "ERROR")
        reason = resp.get("detail", resp.get("reason", ""))

        results.append(make_attack_result(
            attack_type="impersonation",
            target="/v1/qds/verify",
            expected_primary_layer="L3",
            expected_outcome="REJECT",
            actual_outcome=actual_decision,
            detected=actual_decision != "ACCEPT",
            event_id=resp.get("evidence_id"),
            reason=reason,
            parameters={"adversarial_signer_id": adversary, "attempt": i},
            error=raw["error"],
            run_id=run_id,
            started_at=started,
            completed_at=raw["completed_at"],
        ))

    return results


if __name__ == "__main__":
    results = run_impersonation()
    for r in results:
        print_result(r)
    print("\nAggregate:", aggregate_results(results))
