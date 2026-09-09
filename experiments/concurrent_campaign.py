"""
Concurrent Benchmark Campaign (T6).

Evaluates verification throughput and latency scaling under varying concurrency levels:
[1, 5, 10, 20, 50].
Validates that ledger hash-chain integrity is strictly preserved after high-concurrency writes.

Writes results to experiments/results/concurrent_campaign.csv with columns:
concurrency,throughput_rps,p95_latency_ms,chain_valid
"""
import os
import sys
import csv
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ledger.hash_chain import EvidenceLedger
from src.ledger.verifier import verify_ledger


def run_concurrent_campaign(
    concurrency_levels=[1, 5, 10, 20, 50],
    n_ops_per_level: int = 50,
    out_path: str = "experiments/results/concurrent_campaign.csv"
):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    rows = []

    print("=" * 65)
    print("  Q-SENTINEL Concurrent Campaign Benchmark")
    print("=" * 65)

    for c in concurrency_levels:
        db_path = f"data/benchmark_concurrent_{c}.db"
        ledger = EvidenceLedger(db_path=db_path)

        def execute_one(i):
            t0 = time.time()
            event_data = {
                "session_id": f"sess-bench-{c}-{i}-{uuid.uuid4()}",
                "signer_id": "alice_bench",
                "verifier_id": "bob_bench",
                "decision": "ACCEPT" if i % 2 == 0 else "REJECT",
                "findings": [{"bench": True, "idx": i}],
                "timestamp": time.time()
            }
            ledger.record_event(event_data)
            return time.time() - t0

        start_wall = time.time()
        latencies = []
        with ThreadPoolExecutor(max_workers=c) as executor:
            futures = [executor.submit(execute_one, i) for i in range(n_ops_per_level)]
            for f in as_completed(futures):
                latencies.append(f.result())

        total_wall = time.time() - start_wall
        throughput_rps = n_ops_per_level / total_wall if total_wall > 0 else 0.0
        
        latencies_ms = sorted([l * 1000.0 for l in latencies])
        p95_idx = min(len(latencies_ms) - 1, int(0.95 * len(latencies_ms)))
        p95_ms = latencies_ms[p95_idx]

        chain_valid = verify_ledger(db_path=db_path)

        # Cleanup benchmark DB
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except OSError:
            pass

        print(f"Concurrency {c:2d}: Throughput={throughput_rps:.1f} rps, P95={p95_ms:.2f} ms, Chain Valid={chain_valid}")

        rows.append({
            "concurrency": c,
            "throughput_rps": f"{throughput_rps:.2f}",
            "p95_latency_ms": f"{p95_ms:.2f}",
            "chain_valid": chain_valid
        })

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["concurrency", "throughput_rps", "p95_latency_ms", "chain_valid"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")
    return rows


if __name__ == "__main__":
    run_concurrent_campaign()
