"""
L4 — Evidence Ledger Tests.

These tests verify the SHA-256 hash chain, append-only storage,
and tamper detection.
"""
import os
import pytest
import sqlite3
from src.ledger.hash_chain import EvidenceLedger
from src.ledger.verifier import LedgerVerifier


class TestHashChain:
    """Verify hash chain integrity."""

    def setup_method(self):
        self.db_path = "data/test_ledger.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.ledger = EvidenceLedger(db_path=self.db_path)

    def teardown_method(self):
        self.ledger.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_first_event_uses_genesis_hash(self):
        genesis = "0" * 64
        event = {"event_id": "evt-1", "decision": "ACCEPT", "reason": "test"}
        h = self.ledger.record_event(event)
        assert len(h) == 64
        record = self.ledger.get_event("evt-1")
        assert record["previous_hash"] == genesis

    def test_chain_links_sequentially(self):
        self.ledger.record_event({"event_id": "evt-1", "decision": "ACCEPT"})
        self.ledger.record_event({"event_id": "evt-2", "decision": "REJECT"})

        r1 = self.ledger.get_event("evt-1")
        r2 = self.ledger.get_event("evt-2")
        assert r2["previous_hash"] == r1["current_hash"]

    def test_chain_verification_passes_for_intact_chain(self):
        for i in range(5):
            self.ledger.record_event({
                "event_id": f"evt-{i}",
                "decision": "ACCEPT",
                "reason": "baseline"
            })
        verifier = LedgerVerifier(self.ledger)
        result = verifier.verify_chain()
        assert result["valid"] is True
        assert result["records_verified"] == 5

    def test_chain_verification_detects_tampering(self):
        for i in range(3):
            self.ledger.record_event({
                "event_id": f"evt-{i}",
                "decision": "ACCEPT",
                "reason": "baseline"
            })

        # Tamper directly with SQLite
        self.ledger.cursor.execute(
            "UPDATE evidence SET decision = 'REJECT' WHERE event_id = 'evt-1'"
        )
        self.ledger.conn.commit()

        verifier = LedgerVerifier(self.ledger)
        result = verifier.verify_chain()
        assert result["valid"] is False
        assert "evt-1" in result["reason"]

    def test_get_nonexistent_event_returns_none(self):
        assert self.ledger.get_event("nonexistent") is None

    def test_duplicate_event_id_raises(self):
        self.ledger.record_event({"event_id": "evt-dup", "decision": "ACCEPT"})
        with pytest.raises(Exception):
            self.ledger.record_event({"event_id": "evt-dup", "decision": "REJECT"})

    def test_canonical_serialization_excludes_hash_fields(self):
        """Ensure previous_hash and current_hash are NOT included in the canonical event."""
        import json
        import hashlib

        event = {"event_id": "evt-canon", "decision": "ACCEPT", "reason": "test"}
        self.ledger.record_event(event)
        record = self.ledger.get_event("evt-canon")

        # Reconstruct canonical hash
        canonical_fields = {
            k: v for k, v in event.items()
            if k not in ['previous_hash', 'current_hash'] and v is not None
        }
        canonical = json.dumps(canonical_fields, sort_keys=True)
        expected = hashlib.sha256((record["previous_hash"] + canonical).encode()).hexdigest()
        assert record["current_hash"] == expected
