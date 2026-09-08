"""
L4 — Evidence Ledger Tests (v9).

These tests verify the HMAC-SHA256 hash chain, append-only storage,
and tamper detection using the v9 EvidenceLedger.
"""
import os
import uuid
import tempfile
import pytest
import sqlite3
import json
import hashlib
import time
from src.ledger.hash_chain import EvidenceLedger
from src.ledger.verifier import verify_ledger


class TestHashChain:
    """Verify hash chain integrity."""

    def setup_method(self):
        # Use unique temp file per test to avoid Windows file locking issues
        self.db_path = os.path.join(tempfile.gettempdir(), f"test_ledger_{uuid.uuid4().hex}.db")
        self.ledger = EvidenceLedger(db_path=self.db_path)

    def teardown_method(self):
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except PermissionError:
            pass

    def _make_event(self, event_id, decision="ACCEPT"):
        """Helper to create a well-formed event dict."""
        return {
            "event_id": event_id,
            "timestamp": time.time(),
            "session_id": "test-session",
            "signer_id": "alice",
            "verifier_id": "bob",
            "decision": decision,
            "findings": [],
        }

    def test_genesis_block_created(self):
        """The ledger should auto-create a genesis block on init."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM evidence WHERE event_id='genesis'")
            genesis = cursor.fetchone()
            assert genesis is not None
            assert genesis['previous_hash'] == "0" * 64

    def test_first_event_links_to_genesis(self):
        event = self._make_event("evt-1")
        self.ledger.record_event(event)
        record = self.ledger.get_event("evt-1")
        assert record is not None
        assert len(record["current_hash"]) == 64

    def test_chain_links_sequentially(self):
        self.ledger.record_event(self._make_event("evt-1"))
        self.ledger.record_event(self._make_event("evt-2", "REJECT"))

        r1 = self.ledger.get_event("evt-1")
        r2 = self.ledger.get_event("evt-2")
        assert r2["previous_hash"] == r1["current_hash"]

    def test_chain_verification_passes_for_intact_chain(self):
        for i in range(5):
            self.ledger.record_event(self._make_event(f"evt-{i}"))
        assert verify_ledger(self.db_path) is True

    def test_chain_verification_detects_tampering(self):
        for i in range(3):
            self.ledger.record_event(self._make_event(f"evt-{i}"))

        # Tamper directly with SQLite
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE evidence SET decision = 'REJECT' WHERE event_id = 'evt-1'"
            )
            conn.commit()

        assert verify_ledger(self.db_path) is False

    def test_get_nonexistent_event_returns_none(self):
        assert self.ledger.get_event("nonexistent") is None
