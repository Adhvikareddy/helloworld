"""
Unit tests for evidence ledger integrity, concurrency, and checkpoint verification (T5).

Tests:
16. 50 concurrent verifications via ThreadPoolExecutor, then verify_chain() must pass.
17a. Deleting the last 3 ledger rows must be detected by checkpoint verification.
17b. Tampering with an existing ledger row's data/hash is detected by verify_ledger.
"""
import sqlite3
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytest

from src.ledger.hash_chain import EvidenceLedger
from src.ledger.verifier import verify_ledger, verify_chain, verify_checkpoint


def test_concurrent_verifications_maintain_chain_integrity(tmp_path):
    """50 concurrent verifications via ThreadPoolExecutor must maintain valid hash-chain integrity."""
    db_path = str(tmp_path / "concurrent_ledger.db")
    ledger = EvidenceLedger(db_path=db_path)
    
    def record_one_verification(i):
        event_data = {
            "session_id": f"sess-concurrent-{i}",
            "signer_id": "alice",
            "verifier_id": "bob",
            "decision": "ACCEPT" if i % 2 == 0 else "REJECT",
            "findings": [{"test_id": i}],
            "timestamp": time.time()
        }
        return ledger.record_event(event_data)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(record_one_verification, i) for i in range(50)]
        results = [f.result() for f in as_completed(futures)]

    assert len(results) == 50
    assert verify_chain(db_path=db_path) is True
    assert verify_ledger(db_path=db_path) is True


def test_deleting_last_three_rows_detected_by_checkpoint(tmp_path):
    """Deleting the last 3 ledger rows must be detected by checkpoint verification."""
    db_path = str(tmp_path / "checkpoint_ledger.db")
    ledger = EvidenceLedger(db_path=db_path)

    for i in range(6):
        ledger.record_event({
            "session_id": f"sess-{i}",
            "signer_id": "alice",
            "verifier_id": "bob",
            "decision": "ACCEPT",
            "findings": [{"idx": i}],
            "timestamp": time.time()
        })

    checkpoint = ledger.create_checkpoint()
    assert checkpoint is not None
    assert checkpoint["seq_num"] >= 6
    assert verify_checkpoint(checkpoint, db_path=db_path) is True

    # Adversary deletes the last 3 ledger rows (rollback attack)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            DELETE FROM evidence 
            WHERE seq_num IN (
                SELECT seq_num FROM evidence ORDER BY seq_num DESC LIMIT 3
            )
        """)
        conn.commit()

    # Checkpoint verification must FAIL (detecting rollback/truncation)
    assert verify_checkpoint(checkpoint, db_path=db_path) is False


def test_tampered_ledger_row_fails_chain_verification(tmp_path):
    """Modifying decision or hash in an existing row is detected by verify_ledger."""
    db_path = str(tmp_path / "tamper_ledger.db")
    ledger = EvidenceLedger(db_path=db_path)

    for i in range(4):
        ledger.record_event({
            "session_id": f"sess-tamper-{i}",
            "signer_id": "alice",
            "verifier_id": "bob",
            "decision": "REJECT",
            "findings": [{"idx": i}],
            "timestamp": time.time()
        })

    assert verify_ledger(db_path=db_path) is True

    # Tamper with row seq_num=2 by switching decision to ACCEPT
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE evidence SET decision = 'ACCEPT' WHERE seq_num = 2")
        conn.commit()

    # Chain verification must now return False
    assert verify_ledger(db_path=db_path) is False
