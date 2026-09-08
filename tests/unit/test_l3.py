"""
L3 — Security Guard Tests.

These tests verify the allowlist-based identity, authorization, nonce,
timestamp, and replay guards.
"""
import time
import pytest
from src.security.identity import IdentityGuard
from src.security.authorization import AuthorizationGuard
from src.security.nonce import NonceGuard, TimestampGuard
from src.security.replay import ReplayGuard


class TestIdentityGuard:
    """Verify allowlist-based identity binding."""

    def test_registered_signer_passes(self):
        assert IdentityGuard.verify_binding("alice", "sess-123")
        assert IdentityGuard.verify_binding("bob", "sess-456")
        assert IdentityGuard.verify_binding("charlie", "sess-789")
        assert IdentityGuard.verify_binding("david", "sess-000")

    def test_unregistered_signer_fails(self):
        assert not IdentityGuard.verify_binding("impersonator", "sess-123")
        assert not IdentityGuard.verify_binding("eve", "sess-456")
        assert not IdentityGuard.verify_binding("mallory", "sess-789")
        assert not IdentityGuard.verify_binding("oscar", "sess-000")
        assert not IdentityGuard.verify_binding("trudy", "sess-111")

    def test_empty_signer_fails(self):
        assert not IdentityGuard.verify_binding("", "sess-123")

    def test_case_sensitive(self):
        assert not IdentityGuard.verify_binding("Alice", "sess-123")
        assert not IdentityGuard.verify_binding("ALICE", "sess-123")


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


class TestNonceGuard:
    """Verify nonce freshness tracking."""

    def test_first_use_is_fresh(self):
        guard = NonceGuard()
        assert guard.is_fresh("nonce-1")

    def test_second_use_is_stale(self):
        guard = NonceGuard()
        guard.is_fresh("nonce-1")
        assert not guard.is_fresh("nonce-1")

    def test_different_nonces_are_independent(self):
        guard = NonceGuard()
        assert guard.is_fresh("nonce-a")
        assert guard.is_fresh("nonce-b")
        assert not guard.is_fresh("nonce-a")
        assert not guard.is_fresh("nonce-b")

    def test_many_nonces(self):
        guard = NonceGuard()
        for i in range(100):
            assert guard.is_fresh(f"nonce-{i}")
        for i in range(100):
            assert not guard.is_fresh(f"nonce-{i}")


class TestTimestampGuard:
    """Verify timestamp freshness."""

    def test_current_timestamp_is_valid(self):
        assert TimestampGuard.is_valid(time.time())

    def test_recent_timestamp_is_valid(self):
        assert TimestampGuard.is_valid(time.time() - 60)

    def test_stale_timestamp_is_invalid(self):
        assert not TimestampGuard.is_valid(time.time() - 400)

    def test_far_future_timestamp_is_invalid(self):
        assert not TimestampGuard.is_valid(time.time() + 400)

    def test_slight_future_drift_allowed(self):
        # Up to 60s future drift is allowed for clock sync
        assert TimestampGuard.is_valid(time.time() + 30)


class TestReplayGuard:
    """Verify combined replay protection."""

    def test_first_request_passes(self):
        nonce_guard = NonceGuard()
        replay_guard = ReplayGuard(nonce_guard)
        assert replay_guard.check_replay("nonce-1", "sess-1")

    def test_replay_detected(self):
        nonce_guard = NonceGuard()
        replay_guard = ReplayGuard(nonce_guard)
        replay_guard.check_replay("nonce-1", "sess-1")
        assert not replay_guard.check_replay("nonce-1", "sess-1")

    def test_different_nonce_is_not_replay(self):
        nonce_guard = NonceGuard()
        replay_guard = ReplayGuard(nonce_guard)
        replay_guard.check_replay("nonce-1", "sess-1")
        assert replay_guard.check_replay("nonce-2", "sess-1")
