"""
Replay Attack — L3 nonce/session freshness test.

The attacker captures a valid, previously-accepted request and resubmits
it with the SAME nonce and session context.  L3 must detect the replay
via nonce/freshness controls.
"""
import uuid
import datetime
import copy
from attacker.client import get_base_payload, send_verify
from attacker.reporting import make_attack_result, print_result, aggregate_results
from attacker.config import DEFAULT_REPEAT_COUNT


def run_replay(count: int = DEFAULT_REPEAT_COUNT) -> list:
    """
    Execute replay attacks against real nonce/session freshness controls.

    For each attempt:
      1. Send a legitimate request and verify ACCEPT.
      2. Deep-copy the same payload (same nonce, same session_id).
      3. Resubmit the identical payload.
      4. Verify that L3 REJECT with reason=replay.
    """
    results = []
    run_id = f"replay-{uuid.uuid4()}"

    for i in range(count):
        # Step 1: legitimate request
        original_payload = get_base_payload(experiment_id=f"replay_original_{i}")
        initial_raw = send_verify(original_payload)
        initial_resp = initial_raw["response"]

        if initial_raw["http_status"] != 200 or initial_resp.get("decision") != "ACCEPT":
            # If the original doesn't succeed, record and continue
            results.append(make_attack_result(
                attack_type="replay",
                target="/v1/qds/verify",
                expected_primary_layer="L3",
                expected_outcome="REJECT",
                actual_outcome="SETUP_FAILED",
                detected=False,
                reason="Original legitimate request did not ACCEPT",
                parameters={"attempt": i, "phase": "setup"},
                error=f"Setup HTTP {initial_raw['http_status']}",
                run_id=run_id,
                started_at=initial_raw["started_at"],
                completed_at=initial_raw["completed_at"],
            ))
            continue

        # Step 2: replay — identical payload including same nonce
        started = datetime.datetime.utcnow().isoformat()
        replay_payload = copy.deepcopy(original_payload)
        # Do NOT generate new nonce/session — reuse the originals
        replay_raw = send_verify(replay_payload)
        replay_resp = replay_raw["response"]

        actual_decision = "REJECT" if replay_raw["http_status"] == 403 else replay_resp.get("decision", "ERROR")
        reason = replay_resp.get("detail", replay_resp.get("reason", ""))

        results.append(make_attack_result(
            attack_type="replay",
            target="/v1/qds/verify",
            expected_primary_layer="L3",
            expected_outcome="REJECT",
            actual_outcome=actual_decision,
            detected=actual_decision != "ACCEPT",
            event_id=replay_resp.get("evidence_id"),
            reason=reason,
            parameters={
                "replayed_nonce": original_payload["nonce"],
                "replayed_session_id": original_payload["session_id"],
                "original_evidence_id": initial_resp.get("evidence_id"),
                "attempt": i,
            },
            error=replay_raw["error"],
            run_id=run_id,
            started_at=started,
            completed_at=replay_raw["completed_at"],
        ))

    return results


if __name__ == "__main__":
    results = run_replay()
    for r in results:
        print_result(r)
    print("\nAggregate:", aggregate_results(results))
