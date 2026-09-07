"""
Q-SENTINEL Attack Orchestrator.

Usage:
  python -m attacker.runner --attack forgery-a
  python -m attacker.runner --attack forgery-b
  python -m attacker.runner --attack impersonation
  python -m attacker.runner --attack replay
  python -m attacker.runner --attack unauthorized
  python -m attacker.runner --attack channel
  python -m attacker.runner --attack channel --level high --shots 4096
  python -m attacker.runner --attack ledger-tamper
  python -m attacker.runner --attack all
"""
import argparse
import json
import sys

from attacker.scenarios.forgery import run_forgery_a, run_forgery_b, compute_forgery_acceptance
from attacker.scenarios.impersonation import run_impersonation
from attacker.scenarios.replay import run_replay
from attacker.scenarios.unauthorized_verifier import run_unauthorized
from attacker.scenarios.channel import run_channel
from attacker.scenarios.ledger_tamper import run_ledger_tamper
from attacker.reporting import print_result, aggregate_results


ATTACKS = {
    "forgery-a": "Forgery A — Invalid-signature mutation (L1)",
    "forgery-b": "Forgery B — Valid-path adversarial forgery experiment (L1/L2)",
    "impersonation": "Impersonation — Wrong signer identity (L3)",
    "replay": "Replay — Reused nonce/session (L3)",
    "unauthorized": "Unauthorized Verification — Unregistered verifier (L3)",
    "channel": "Channel Manipulation — Quantum disturbance (L2)",
    "ledger-tamper": "Ledger Tampering — Hash-chain integrity (L4)",
}


def execute(attack: str, args) -> list:
    if attack == "forgery-a":
        return run_forgery_a(count=args.count)
    elif attack == "forgery-b":
        return run_forgery_b(count=args.count)
    elif attack == "impersonation":
        return run_impersonation(count=args.count)
    elif attack == "replay":
        return run_replay(count=args.count)
    elif attack == "unauthorized":
        return run_unauthorized(count=args.count)
    elif attack == "channel":
        levels = [args.level] if args.level else None
        return run_channel(levels=levels, shots=args.shots, repeats=args.count)
    elif attack == "ledger-tamper":
        return run_ledger_tamper()
    else:
        print(f"Unknown attack: {attack}", file=sys.stderr)
        return []


def main():
    parser = argparse.ArgumentParser(description="Q-SENTINEL Attack Orchestrator")
    parser.add_argument("--attack", required=True,
                        choices=list(ATTACKS.keys()) + ["all"],
                        help="Attack scenario to execute")
    parser.add_argument("--count", type=int, default=5,
                        help="Number of attempts per attack")
    parser.add_argument("--level", default=None,
                        help="Channel disturbance level (low/medium/high)")
    parser.add_argument("--shots", type=int, default=1024,
                        help="Shot count for quantum measurements")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON array")
    args = parser.parse_args()

    attacks_to_run = list(ATTACKS.keys()) if args.attack == "all" else [args.attack]

    all_results = []
    for atk in attacks_to_run:
        print(f"\n{'='*60}")
        print(f"  {ATTACKS[atk]}")
        print(f"{'='*60}")
        results = execute(atk, args)
        all_results.extend(results)

        if not args.json:
            for r in results:
                print_result(r)
            agg = aggregate_results(results)
            print(f"\n  Summary: {agg}")
            if atk == "forgery-b":
                print(f"  Forgery acceptance: {compute_forgery_acceptance(results)}")

    if args.json:
        print(json.dumps(all_results, indent=2, default=str))


if __name__ == "__main__":
    main()
