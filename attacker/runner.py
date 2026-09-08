"""
Q-SENTINEL Attack Execution Script.

Runs all CLI attack scenarios against the live API or testbed environment.
Demonstrates genuine causal attack generation and real multi-layer detection.
"""
import time
import requests
from src.transport.client import TransportClient
from attacker.harness import AttackerHarness
from attacker.scenarios.forgery import run_forgery_a, run_forgery_b, compute_forgery_acceptance
from attacker.scenarios.impersonation import run_impersonation
from attacker.scenarios.unauthorized_verifier import run_unauthorized
from attacker.scenarios.replay import run_replay
from attacker.scenarios.channel import run_channel
from attacker.scenarios.ledger_tamper import run_ledger_tamper
from attacker.scenarios.timing_oracle import run_timing_oracle
from attacker.scenarios.adaptive_x import run_adaptive_x_test
from attacker.reporting import print_result, aggregate_results
from attacker.client import get_base_payload, send_verify


def run_all_attacks():
    client = TransportClient("http://localhost:8000")
    harness = AttackerHarness()
    
    print("\n========================================================")
    print("      Q-SENTINEL CLI ADVERSARIAL SUITE RUNNER           ")
    print("========================================================")
    
    # 0. Health check
    for i in range(5):
        try:
            r = requests.get("http://localhost:8000/v1/health", timeout=2.0)
            if r.status_code == 200:
                print(f"[+] API Health check passed: {r.json()}")
                break
        except Exception:
            time.sleep(1)
            
    # 1. Baseline Legitimate Verification
    print("\n--- [1/9] Baseline Honest Verification (Honest Alice -> Bob) ---")
    legit_payload = get_base_payload(signer_id="alice", verifier_id="bob", disturbance=0.0)
    legit_res = send_verify(legit_payload)
    print(f"Decision: {legit_res['response'].get('decision')} (Expected: ACCEPT)")
    print(f"Latency:  {legit_res['response'].get('latency_ms', 0):.2f} ms")

    # 2. Forgery A (Quantum key bit manipulation)
    print("\n--- [2/9] Scenario: Forgery A (Mutated Quantum Keys) ---")
    forgery_a_results = run_forgery_a(count=3)
    for r in forgery_a_results:
        print_result(r)
    agg_a = aggregate_results(forgery_a_results)
    print(f"Aggregate: {agg_a['detected']}/{agg_a['total_attempts']} detected (Detection Rate: {agg_a['detection_rate']:.1%})")

    # 3. Forgery B (Valid-Path Perturbation Experiment)
    print("\n--- [3/9] Scenario: Forgery B (Empirical Adversarial Experiment) ---")
    forgery_b_results = run_forgery_b(count=5)
    for r in forgery_b_results:
        print_result(r)
    acceptance_stats = compute_forgery_acceptance(forgery_b_results)
    print(f"Stats: Total={acceptance_stats['total_forgery_attempts']}, Accepted={acceptance_stats['accepted_forgery_attempts']}, Rejected={acceptance_stats['rejected_forgery_attempts']}")

    # 4. Impersonation Attack
    print("\n--- [4/9] Scenario: Impersonation Attack ---")
    impersonation_results = run_impersonation(count=3)
    for r in impersonation_results:
        print_result(r)
    agg_imp = aggregate_results(impersonation_results)
    print(f"Aggregate: {agg_imp['detected']}/{agg_imp['total_attempts']} detected")

    # 5. Unauthorized Verifier
    print("\n--- [5/9] Scenario: Unauthorized Verifier ---")
    unauth_results = run_unauthorized(count=3)
    for r in unauth_results:
        print_result(r)
    agg_unauth = aggregate_results(unauth_results)
    print(f"Aggregate: {agg_unauth['detected']}/{agg_unauth['total_attempts']} detected")

    # 6. Replay Attack
    print("\n--- [6/9] Scenario: Replay Attack ---")
    replay_results = run_replay(count=2)
    for r in replay_results:
        print_result(r)
    agg_rep = aggregate_results(replay_results)
    print(f"Aggregate: {agg_rep['detected']}/{agg_rep['total_attempts']} detected")

    # 7. Channel Manipulation
    print("\n--- [7/9] Scenario: Channel Manipulation ---")
    channel_results = run_channel(repeats=2)
    for r in channel_results:
        print_result(r)
    agg_chan = aggregate_results(channel_results)
    print(f"Aggregate: {agg_chan['detected']}/{agg_chan['total_attempts']} detected")

    # 8. Ledger Tamper (Integrity Audit)
    print("\n--- [8/9] Scenario: Ledger Tampering & Hash-Chain Audit ---")
    ledger_results = run_ledger_tamper()
    for r in ledger_results:
        print_result(r)

    # 9. Timing Oracle & Adaptive Regressions
    print("\n--- [9/9] Scenario: Timing Oracle & Adaptive Disturbance ---")
    valid_p = get_base_payload(signer_id="alice", verifier_id="bob")
    invalid_p = harness.impersonate_alice()
    run_timing_oracle(client, valid_p, invalid_p)
    run_adaptive_x_test(client)

    print("\n========================================================")
    print("      ALL ATTACK RUNNER SCENARIOS COMPLETED             ")
    print("========================================================\n")


if __name__ == "__main__":
    run_all_attacks()
