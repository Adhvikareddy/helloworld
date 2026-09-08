"""
L3 — Security Guard Tests (v9).

These tests verify the PQC identity manager, SQLite-backed nonce guard,
and timestamp freshness guard.
"""
import time
import os
import uuid
import tempfile
import pytest
from src.security.identity import PQCIdentityManager
from src.security.authorization import AuthorizationGuard
from src.security.nonce import SQLiteNonceGuard, TimestampGuard


class TestPQCIdentityManager:
    """Verify PQC-based identity management."""

    def setup_method(self):
        self.manager = PQCIdentityManager()
        # Register test participants with dummy keys
        self.manager.register_participant("alice", b"pk_alice", is_verifier=True)
        self.manager.register_participant("bob", b"pk_bob", is_verifier=True)

    def test_registered_participant_has_key(self):
        assert self.manager.get_public_key("alice") == b"pk_alice"
        assert self.manager.get_public_key("bob") == b"pk_bob"

    def test_unregistered_participant_returns_none(self):
        assert self.manager.get_public_key("unknown") is None
        assert self.manager.get_public_key("mallory") is None

    def test_verifier_authorization(self):
        assert self.manager.is_verifier_authorized("alice")
        assert self.manager.is_verifier_authorized("bob")

    def test_non_verifier_not_authorized(self):
        self.manager.register_participant("charlie", b"pk_charlie", is_verifier=False)
        assert not self.manager.is_verifier_authorized("charlie")

    def test_empty_name_not_authorized(self):
        assert not self.manager.is_verifier_authorized("")


class TestAuthorizationGuard:
    """Verify allowlist-based verifier authorization."""

    def test_authorized_verifier_passes(self):
        assert AuthorizationGuard.is_authorized("bob")
        assert AuthorizationGuard.is_authorized("alice")

    def test_unauthorized_verifier_fails(self):
        assert not AuthorizationGuard.is_authorized("unauthorized_verifier")
        assert not AuthorizationGuard.is_authorized("eve")
        assert not AuthorizationGuard.is_authorized("unregistered_node")
        assert not AuthorizationGuard.is_authorized("revoked_verifier")
        assert not AuthorizationGuard.is_authorized("external_agent")

    def test_empty_verifier_fails(self):
        assert not AuthorizationGuard.is_authorized("")


class TestSQLiteNonceGuard:
    """Verify SQLite-backed nonce freshness tracking."""

    def setup_method(self):
        # Use unique temp file per test to avoid Windows file locking issues
        self.db_path = os.path.join(tempfile.gettempdir(), f"test_nonces_{uuid.uuid4().hex}.db")
        self.guard = SQLiteNonceGuard(db_path=self.db_path)

    def teardown_method(self):
        # Best-effort cleanup; Windows may still hold the file briefly
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except PermissionError:
            pass

    def test_first_use_is_fresh(self):
        assert self.guard.is_fresh("nonce-1", "session-1")

    def test_second_use_is_stale(self):
        self.guard.is_fresh("nonce-1", "session-1")
        assert not self.guard.is_fresh("nonce-1", "session-1")

    def test_different_nonces_are_independent(self):
        assert self.guard.is_fresh("nonce-a", "session-1")
        assert self.guard.is_fresh("nonce-b", "session-1")
        assert not self.guard.is_fresh("nonce-a", "session-1")
        assert not self.guard.is_fresh("nonce-b", "session-1")

    def test_many_nonces(self):
        for i in range(100):
            assert self.guard.is_fresh(f"nonce-{i}", "session-bulk")
        for i in range(100):
            assert not self.guard.is_fresh(f"nonce-{i}", "session-bulk")


class TestTimestampGuard:
    """Verify timestamp freshness."""

    def test_current_timestamp_is_valid(self):
        assert TimestampGuard.is_valid(time.time())

    def test_recent_timestamp_is_valid(self):
        assert TimestampGuard.is_valid(time.time() - 30)

    def test_stale_timestamp_is_invalid(self):
        assert not TimestampGuard.is_valid(time.time() - 400)

    def test_far_future_timestamp_is_invalid(self):
        assert not TimestampGuard.is_valid(time.time() + 400)

    def test_slight_future_drift_allowed(self):
        # Up to 60s future drift is allowed for clock sync
        assert TimestampGuard.is_valid(time.time() + 30)
