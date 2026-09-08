#!/usr/bin/env python3
"""
Q-SENTINEL End-to-End Acceptance Smoke Test.
Verifies all 7 phases against the live server:
  1. Calibration on startup (not 'uncalibrated')
  2. Legitimate distribute -> reveal -> verify flow (ACCEPT)
  3. Attack scenarios (forgery, replay, impersonation, unauthorized, channel) caught with correct layer findings
  4. Live ledger events feed (GET /v1/ledger/events)
  5. Cryptographic hash-chain audit (GET /v1/ledger/verify-chain -> chain_valid: True)
  6. DB tampering demo (POST /v1/ledger/tamper -> verify-chain -> chain_valid: False)
  7. Zero 404s / 500s across the entire run.
"""
import sys
import os
import time
import uuid
import requests

sys.path.insert(0, os.path.abspath("."))

BASE_URL = "http://localhost:8000"
ERRORS = []
HTTP_STATUSES = []

def track_request(method, url, **kwargs):
    kwargs.setdefault("timeout", 15.0)
    resp = requests.request(method, url, **kwargs)
    HTTP_STATUSES.append((method, url, resp.status_code))
    if resp.status_code in [404, 500, 502]:
        ERRORS.append(f"Unexpected HTTP {resp.status_code} on {method} {url}: {resp.text[:120]}")
    return resp

def assert_true(cond, msg):
    if not cond:
        print(f"  [FAIL] {msg}")
        ERRORS.append(msg)
    else:
        print(f"  [PASS] {msg}")

def reset_ledger_for_test():
    """Ensure ledger starts from a clean, mathematically valid genesis block."""
    import sqlite3, hmac, hashlib, os
    db_path = os.environ.get("QSENTINEL_DB_PATH", "data/ledger.db")
    if not os.path.exists(db_path):
        return
    LEDGER_SECRET = os.environ.get("QSENTINEL_LEDGER_SECRET", "default_insecure_secret_for_demo").encode('utf-8')
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute("DELETE FROM evidence")
            try:
                conn.execute("DELETE FROM sqlite_sequence WHERE name='evidence'")
            except Exception:
                pass
            genesis_hash = "0" * 64
            genesis_sig = hmac.new(LEDGER_SECRET, genesis_hash.encode(), hashlib.sha256).hexdigest()
            conn.execute('''
                INSERT INTO evidence (
                    seq_num, event_id, timestamp, session_id, signer_id, verifier_id,
                    decision, findings, experiment_id, previous_hash, current_hash, signature
                ) VALUES (0, 'genesis', 0.0, 'genesis', 'genesis', 'genesis', 'ACCEPT', '[]', 'genesis', ?, ?, ?)
            ''', (genesis_hash, genesis_hash, genesis_sig))
            conn.commit()
    except Exception as e:
        print(f"  [WARN] Ledger reset: {e}")

def main():
    print("\n========================================================")
    print("      Q-SENTINEL END-TO-END ACCEPTANCE SMOKE TEST       ")
    print("========================================================")

    # 0. Health check & clean state setup
    print("\n[Step 0] API Health Check & Ledger State Setup")
    reset_ledger_for_test()
    resp = track_request("GET", f"{BASE_URL}/v1/health")
    assert_true(resp.status_code == 200, "API health returned 200")
    print(f"  Response: {resp.json()}")

    # 1. Calibration state check
    print("\n[Step 1] System Calibration State")
    resp = track_request("GET", f"{BASE_URL}/v1/calibration/status")
    assert_true(resp.status_code == 200, "Calibration status returned 200")
    cdata = resp.json()
    baseline = cdata.get("baseline_version", "")
    assert_true(baseline != "uncalibrated" and bool(baseline), f"System is calibrated: baseline_version='{baseline}'")
    print(f"  Baseline: {baseline}, Thresholds: ({cdata.get('threshold_low')}, {cdata.get('threshold_high')})")

    # 2. Legitimate pipeline: distribute -> reveal -> verify
    print("\n[Step 2] Legitimate Verification Pipeline (Alice -> Bob)")
    from attacker.client import get_base_payload
    payload = get_base_payload(signer_id="alice", verifier_id="bob", disturbance=0.0)
    v_resp = track_request("POST", f"{BASE_URL}/v1/qds/verify", json=payload, headers={"x-role": "auditor"})
    assert_true(v_resp.status_code == 200, "Legitimate verify returned HTTP 200")
    v_data = v_resp.json()
    assert_true(v_data.get("decision") == "ACCEPT", f"Legitimate verification ACCEPTED (got {v_data.get('decision')})")
    assert_true(bool(v_data.get("evidence_id")), f"Evidence recorded with ID: {v_data.get('evidence_id')}")
    assert_true(v_data.get("latency_ms", 0) >= 30.0, f"Constant-time latency floor enforced: {v_data.get('latency_ms', 0):.1f}ms")

    # 3. Attack Scenarios via /v1/testbed/attack/{scenario}
    print("\n[Step 3] Live Attack Scenarios via Testbed")
    test_scenarios = [
        ("forgery", "REJECT", ["StatisticalProbe", "L2", "mismatch", "quantum"]),
        ("replay", "REJECT", ["DoubleConsumptionGuard", "FreshnessProbe", "L3", "Nonce"]),
        ("impersonation", "REJECT", ["AuthenticationProbe", "L3", "identity", "signature"]),
        ("unauthorized", "REJECT", ["AuthenticationProbe", "L3", "authorized"]),
        ("channel", ["REJECT", "QUARANTINE"], ["StatisticalProbe", "TomographyProbe", "L2", "quantum"]),
    ]

    for scenario, expected_outcome, expected_keywords in test_scenarios:
        t_resp = track_request("POST", f"{BASE_URL}/v1/testbed/attack/{scenario}")
        assert_true(t_resp.status_code == 200, f"Attack scenario '{scenario}' returned HTTP 200")
        t_data = t_resp.json()
        outcome = t_data.get("actual_outcome")
        if isinstance(expected_outcome, list):
            outcome_match = outcome in expected_outcome
        else:
            outcome_match = (outcome == expected_outcome)
        assert_true(outcome_match, f"Scenario '{scenario}' outcome: {outcome} (expected {expected_outcome})")
        assert_true(t_data.get("detected") is True, f"Scenario '{scenario}' detected flag is True")

        # Check findings keywords
        findings_str = str(t_data.get("findings", [])) + " " + t_data.get("reason", "")
        keyword_found = any(k.lower() in findings_str.lower() for k in expected_keywords)
        assert_true(keyword_found, f"Scenario '{scenario}' findings reference target detector ({expected_keywords})")

    # 4. Ledger Events Feed
    print("\n[Step 4] Live Ledger Events Feed (GET /v1/ledger/events?limit=50)")
    e_resp = track_request("GET", f"{BASE_URL}/v1/ledger/events?limit=50")
    raw_json = e_resp.json()
    events = raw_json if isinstance(raw_json, list) else raw_json.get("events", [])
    assert_true(len(events) >= 6, f"Ledger contains events from steps 2-3 (count={len(events)})")
    if events:
        latest = events[0]
        has_id = ("evidence_id" in latest or "event_id" in latest) and "decision" in latest
        eid = latest.get("evidence_id") or latest.get("event_id")
        assert_true(has_id, f"Latest event format valid: {eid} -> {latest.get('decision')}")

    # 5. Ledger Integrity Hash Chain Audit (Before Tampering)
    print("\n[Step 5] Cryptographic Hash-Chain Audit (Pre-Tamper)")
    ch_resp = track_request("GET", f"{BASE_URL}/v1/ledger/verify-chain")
    assert_true(ch_resp.status_code == 200, "Ledger verify-chain returned HTTP 200")
    ch_data = ch_resp.json()
    assert_true(ch_data.get("chain_valid") is True, f"Cryptographic HMAC chain valid: {ch_data}")

    # 6. Database Tampering Demo
    print("\n[Step 6] Database Tampering Demo & Tamper Detection")
    tamp_resp = track_request("POST", f"{BASE_URL}/v1/ledger/tamper")
    assert_true(tamp_resp.status_code == 200, "Tamper endpoint returned HTTP 200")
    tamp_data = tamp_resp.json()
    assert_true(tamp_data.get("status") == "TAMPERED", f"Tamper executed successfully: {tamp_data}")

    # Re-audit chain after tamper
    post_ch_resp = track_request("GET", f"{BASE_URL}/v1/ledger/verify-chain")
    assert_true(post_ch_resp.status_code == 200, "Post-tamper verify-chain returned HTTP 200")
    post_ch_data = post_ch_resp.json()
    assert_true(post_ch_data.get("chain_valid") is False, f"Tamper genuinely detected! chain_valid=False (broken_at={post_ch_data.get('broken_at')})")

    # 7. Confirm zero 404s or 500s across the whole run
    print("\n[Step 7] Full Stack Contract & Route Verification")
    bad_statuses = [s for s in HTTP_STATUSES if s[2] in [404, 500, 502]]
    assert_true(len(bad_statuses) == 0, f"Zero 404/500/502 status codes encountered (total calls={len(HTTP_STATUSES)})")

    print("\n========================================================")
    if not ERRORS:
        print("   >>> ALL E2E ACCEPTANCE SMOKE TESTS PASSED (7/7) <<<  ")
        print("========================================================\n")
        return 0
    else:
        print(f"   >>> {len(ERRORS)} TESTS FAILED <<<")
        for e in ERRORS:
            print(f"   - {e}")
        print("========================================================\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
