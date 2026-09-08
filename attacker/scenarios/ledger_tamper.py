"""
Ledger Tampering — L4 integrity experiment.

This is NOT a protocol attack.  It is a separate ledger-integrity test.

Steps:
  1. Create a legitimate verification event so the ledger has content.
  2. Directly modify a stored evidence field in the SQLite database.
  3. Leave the hash chain as-is (do NOT recompute hashes).
  4. Execute ledger chain verification via the API.
  5. Verify that the hash chain detects the modification.

The attacker container requires a shared volume mount to the SQLite
database so it can simulate a storage-layer compromise.
"""
import sqlite3
import uuid
import datetime
from attacker.client import get_base_payload, send_verify, verify_chain
from attacker.reporting import make_attack_result, print_result
from attacker.config import DB_PATH


def run_ledger_tamper() -> list:
    """
    Execute ledger tampering and verify integrity detection.
    """
    results = []
    run_id = f"ledger-tamper-{uuid.uuid4()}"

    # Step 1 — Create a legitimate event
    started = datetime.datetime.utcnow().isoformat()
    payload = get_base_payload(experiment_id=f"ledger_tamper_setup")
    setup_raw = send_verify(payload)
    setup_resp = setup_raw["response"]
    original_event_id = setup_resp.get("evidence_id")
    original_decision = setup_resp.get("decision")

    if setup_raw["http_status"] != 200:
        results.append(make_attack_result(
            attack_type="ledger_tamper",
            target="L4 ledger",
            expected_primary_layer="L4",
            expected_outcome="integrity_violation",
            actual_outcome="SETUP_FAILED",
            detected=False,
            reason="Could not create initial ledger event",
            error=f"HTTP {setup_raw['http_status']}",
            run_id=run_id,
            started_at=started,
            completed_at=setup_raw["completed_at"],
        ))
        return results

    # Step 2 — Tamper directly with SQLite
    tamper_field = "decision"
    tamper_value = "REJECT" if original_decision == "ACCEPT" else "ACCEPT"

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Use a subquery since SQLite does not support LIMIT in UPDATE
        cursor.execute(
            "UPDATE evidence SET decision = ? "
            "WHERE seq_num = (SELECT seq_num FROM evidence ORDER BY seq_num DESC LIMIT 1)",
            (tamper_value,)
        )
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
    except Exception as exc:
        results.append(make_attack_result(
            attack_type="ledger_tamper",
            target="L4 ledger",
            expected_primary_layer="L4",
            expected_outcome="integrity_violation",
            actual_outcome="TAMPER_FAILED",
            detected=False,
            reason="Could not modify ledger DB",
            error=str(exc),
            run_id=run_id,
            started_at=started,
        ))
        return results

    # Step 3 — Verify chain via API
    chain_result = verify_chain()
    chain_valid = chain_result.get("valid", True)
    integrity_violated = not chain_valid

    results.append(make_attack_result(
        attack_type="ledger_tamper",
        target="L4 ledger",
        expected_primary_layer="L4",
        expected_outcome="integrity_violation",
        actual_outcome="integrity_violation" if integrity_violated else "chain_valid_UNEXPECTED",
        detected=integrity_violated,
        event_id=original_event_id,
        reason=chain_result.get("reason", ""),
        parameters={
            "tampered_field": tamper_field,
            "original_value": original_decision,
            "tampered_value": tamper_value,
            "rows_affected": rows_affected,
        },
        error=None,
        run_id=run_id,
        started_at=started,
        completed_at=datetime.datetime.utcnow().isoformat(),
    ))

    return results


if __name__ == "__main__":
    results = run_ledger_tamper()
    for r in results:
        print_result(r)
