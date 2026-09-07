from src.security.identity import IdentityGuard
from src.security.authorization import AuthorizationGuard
from src.security.nonce import NonceGuard, TimestampGuard
import time

def test_identity():
    assert IdentityGuard.verify_binding("alice", "sess")
    assert not IdentityGuard.verify_binding("impersonator", "sess")

def test_authorization():
    assert AuthorizationGuard.is_authorized("bob")
    assert not AuthorizationGuard.is_authorized("unauthorized_verifier")

def test_nonce():
    guard = NonceGuard()
    assert guard.is_fresh("nonce1")
    assert not guard.is_fresh("nonce1")
    assert guard.is_fresh("nonce2")

def test_timestamp():
    assert TimestampGuard.is_valid(time.time())
    assert not TimestampGuard.is_valid(time.time() - 400)
    assert not TimestampGuard.is_valid(time.time() + 400)
