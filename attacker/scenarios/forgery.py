"""
Forgery Attack — two distinct modes as required by Q-SENTINEL v8.

Forgery A — Invalid-signature mutation:
  Start with a valid QDS request, mutate after signing, submit.
  L1 QDS validity must reject.  L2 must NOT be credited.

Forgery B — Valid-path adversarial forgery experiment:
  Predeclared population of attacker-generated requests that pass through
  the full verification pipeline.  Measures empirical forgery-acceptance
  probability P_forge,emp.  This is an empirical detector result, NOT a
  formal QDS security bound.
"""
import uuid
import datetime
from attacker.client import get_base_payload, send_verify
from attacker.reporting import make_attack_result, print_result, aggregate_results
from attacker.config import FORGERY_B_POPULATION, DISTURBANCE_LEVELS, DEFAULT_REPEAT_COUNT


# ---------------------------------------------------------------------------
# Forgery A — Invalid-signature mutation
# ---------------------------------------------------------------------------

def run_forgery_a(count: int = DEFAULT_REPEAT_COUNT) -> list:
    """
    Execute Forgery A: mutate a signed message AFTER signing.

    Steps per attempt:
      1. Construct a legitimate payload (as if genuinely signed).
      2. Set is_invalid_signature=True to signal that the payload was
         tampered after signing — L1 QDS validity must reject.
      3. Submit via normal API.
      4. Verify REJECT with reason=invalid_qds_signature.
    """
    results = []
    run_id = f"forgery-a-{uuid.uuid4()}"
    for i in range(count):
        started = datetime.datetime.utcnow().isoformat()
        payload = get_base_payload(experiment_id=f"forgery_a_{i}")
        # Mutation AFTER signing — makes the signature invalid
        payload["message_digest"] = "TAMPERED_" + payload["message_digest"]
        payload["is_invalid_signature"] = True

        raw = send_verify(payload)
        resp = raw["response"]
        actual_decision = resp.get("decision", "ERROR")
        reason = resp.get("reason", "")

        # L3 attacks return 403, L1 returns 200 with REJECT
        if raw["http_status"] == 403:
            actual_decision = "REJECT"
            reason = resp.get("detail", "")

        results.append(make_attack_result(
            attack_type="forgery_a",
            target="/v1/qds/verify",
            expected_primary_layer="L1",
            expected_outcome="REJECT",
            actual_outcome=actual_decision,
            detected=actual_decision != "ACCEPT",
            event_id=resp.get("evidence_id"),
            reason=reason,
            parameters={"mutated_digest": True, "attempt": i},
            error=raw["error"],
            run_id=run_id,
            started_at=started,
            completed_at=raw["completed_at"],
        ))
    return results


# ---------------------------------------------------------------------------
# Forgery B — Valid-path adversarial forgery experiment
# ---------------------------------------------------------------------------

def run_forgery_b(count: int = FORGERY_B_POPULATION,
                  disturbance: float = DISTURBANCE_LEVELS["medium"]) -> list:
    """
    Execute Forgery B: predeclared valid-path forgery population.

    Each attempt introduces a channel-level disturbance simulating an
    attacker who can partially influence the quantum channel but whose
    payload still passes L1 QDS validity.  The full L1→L2 pipeline
    decides ACCEPT/NOT-ACCEPT.

    The empirical forgery-acceptance probability is computed from results:
      P_forge,emp = accepted / total

    This is NOT a formal QDS security bound.
    """
    results = []
    run_id = f"forgery-b-{uuid.uuid4()}"
    for i in range(count):
        started = datetime.datetime.utcnow().isoformat()
        payload = get_base_payload(experiment_id=f"forgery_b_{i}")
        # Valid-path forgery: signature IS valid, but the attacker
        # introduces a disturbance to try to pass detection.
        payload["disturbance_prob"] = disturbance

        raw = send_verify(payload)
        resp = raw["response"]
        actual_decision = resp.get("decision", "ERROR")

        if raw["http_status"] == 403:
            actual_decision = "REJECT"

        results.append(make_attack_result(
            attack_type="forgery_b",
            target="/v1/qds/verify",
            expected_primary_layer="L1/L2",
            expected_outcome="measured",
            actual_outcome=actual_decision,
            detected=actual_decision != "ACCEPT",
            event_id=resp.get("evidence_id"),
            reason=resp.get("reason"),
            parameters={"disturbance_prob": disturbance, "attempt": i},
            measurements={
                "deviation_score": resp.get("deviation_score"),
                "chi_square": resp.get("chi_square"),
                "threshold_low": resp.get("threshold_low"),
                "threshold_high": resp.get("threshold_high"),
            },
            error=raw["error"],
            run_id=run_id,
            started_at=started,
            completed_at=raw["completed_at"],
        ))

    return results


def compute_forgery_acceptance(results: list) -> dict:
    """
    Compute empirical valid-path forgery-acceptance probability.

    IMPORTANT: This is an empirical detector metric under the tested
    threat model.  It is NOT a formal QDS forgery-security bound,
    NOT an information-theoretic guarantee, and NOT a proof of
    protocol security.
    """
    total = len(results)
    accepted = sum(1 for r in results if r["actual_outcome"] == "ACCEPT")
    return {
        "label": "EMPIRICAL VALID-PATH FORGERY ACCEPTANCE EXPERIMENT",
        "total_forgery_attempts": total,
        "accepted_forgery_attempts": accepted,
        "rejected_forgery_attempts": total - accepted,
        "P_forge_emp": accepted / total if total > 0 else None,
        "note": "This is an empirical detector result, NOT a formal QDS security bound.",
    }


if __name__ == "__main__":
    print("=== FORGERY A ===")
    fa = run_forgery_a()
    for r in fa:
        print_result(r)
    print("\nAggregate:", aggregate_results(fa))

    print("\n=== FORGERY B ===")
    fb = run_forgery_b()
    for r in fb:
        print_result(r)
    print("\nAggregate:", aggregate_results(fb))
    print("\nForgery Acceptance:", compute_forgery_acceptance(fb))
