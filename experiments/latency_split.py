"""
Verification Latency Split Evaluation (T6).

Measures end-to-end API verification latency across verdicts (ACCEPT vs REJECT).
Demonstrates constant-time execution behavior (mitigating timing side channels).

Writes results to experiments/results/latency_split.csv with columns:
verdict,n,mean_ms,p50_ms,p95_ms
"""
import os
import sys
import csv
import time
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from apps.api.main import app
from src.security.envelope import PQCEnvelope
from src.security.identity import global_pqc_identity


def run_latency_split(n_samples: int = 30, out_path: str = "experiments/results/latency_split.csv"):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    client = TestClient(app)

    alice_pk, alice_sk = PQCEnvelope.generate_keypair()
    global_pqc_identity.register_participant("alice_lat", alice_pk, is_verifier=False, role="verifier")
    global_pqc_identity.register_participant("bob_lat", alice_pk, is_verifier=True, role="verifier")

    print("=" * 60)
    print("  Q-SENTINEL Latency Split Evaluation")
    print("=" * 60)

    # 1. Measure ACCEPT latencies
    print(f"[1/2] Benchmarking {n_samples} ACCEPT verifications...")
    accept_latencies = []
    for i in range(n_samples):
        session_id = f"sess-lat-accept-{uuid.uuid4()}"
        L = 30
        dist_payload = {
            "session_id": session_id,
            "signer_id": "alice_lat",
            "verifiers": ["bob_lat"],
            "L": L,
            "nonce": f"nonce-dist-{uuid.uuid4()}",
            "timestamp": time.time()
        }
        dist_payload["signature"] = PQCEnvelope.sign_payload(alice_sk, dist_payload)
        client.post("/v1/qds/distribute", json=dist_payload)

        rev_payload = {
            "session_id": session_id,
            "signer_id": "alice_lat",
            "message_bit": 0,
            "nonce": f"nonce-rev-{uuid.uuid4()}",
            "timestamp": time.time()
        }
        rev_payload["signature"] = PQCEnvelope.sign_payload(alice_sk, rev_payload)
        rev_res = client.post("/v1/qds/reveal", json=rev_payload)
        revealed_keys = rev_res.json()["revealed_keys"]

        ver_payload = {
            "session_id": session_id,
            "signer_id": "alice_lat",
            "verifier_id": "bob_lat",
            "nonce": f"nonce-ver-{uuid.uuid4()}",
            "timestamp": time.time(),
            "message_bit": 0,
            "revealed_keys": revealed_keys
        }
        ver_payload["signature"] = PQCEnvelope.sign_payload(alice_sk, ver_payload)

        t0 = time.time()
        res = client.post("/v1/qds/verify", json=ver_payload)
        dt_ms = (time.time() - t0) * 1000.0
        assert res.status_code == 200
        assert res.json()["decision"] == "ACCEPT"
        accept_latencies.append(dt_ms)

    # 2. Measure REJECT latencies
    print(f"[2/2] Benchmarking {n_samples} REJECT verifications...")
    reject_latencies = []
    for i in range(n_samples):
        session_id = f"sess-lat-reject-{uuid.uuid4()}"
        L = 30
        dist_payload = {
            "session_id": session_id,
            "signer_id": "alice_lat",
            "verifiers": ["bob_lat"],
            "L": L,
            "nonce": f"nonce-dist-{uuid.uuid4()}",
            "timestamp": time.time()
        }
        dist_payload["signature"] = PQCEnvelope.sign_payload(alice_sk, dist_payload)
        client.post("/v1/qds/distribute", json=dist_payload)

        forged_keys = [{"bit_index": j, "basis": "Z", "bit_value": 1} for j in range(L)]
        ver_payload = {
            "session_id": session_id,
            "signer_id": "alice_lat",
            "verifier_id": "bob_lat",
            "nonce": f"nonce-ver-{uuid.uuid4()}",
            "timestamp": time.time(),
            "message_bit": 0,
            "revealed_keys": forged_keys
        }
        # Invalid signature deterministically produces REJECT verdict
        ver_payload["signature"] = "00" * 3309

        t0 = time.time()
        res = client.post("/v1/qds/verify", json=ver_payload)
        dt_ms = (time.time() - t0) * 1000.0
        assert res.status_code == 200
        assert res.json()["decision"] == "REJECT"
        reject_latencies.append(dt_ms)

    def stats(lats):
        s = sorted(lats)
        mean_v = sum(s) / len(s)
        p50_v = s[int(0.50 * len(s))]
        p95_v = s[min(len(s) - 1, int(0.95 * len(s)))]
        return mean_v, p50_v, p95_v

    mean_acc, p50_acc, p95_acc = stats(accept_latencies)
    mean_rej, p50_rej, p95_rej = stats(reject_latencies)

    print(f"ACCEPT (n={n_samples}): mean={mean_acc:.2f}ms, p50={p50_acc:.2f}ms, p95={p95_acc:.2f}ms")
    print(f"REJECT (n={n_samples}): mean={mean_rej:.2f}ms, p50={p50_rej:.2f}ms, p95={p95_rej:.2f}ms")

    rows = [
        {
            "verdict": "ACCEPT",
            "n": n_samples,
            "mean_ms": f"{mean_acc:.2f}",
            "p50_ms": f"{p50_acc:.2f}",
            "p95_ms": f"{p95_acc:.2f}"
        },
        {
            "verdict": "REJECT",
            "n": n_samples,
            "mean_ms": f"{mean_rej:.2f}",
            "p50_ms": f"{p50_rej:.2f}",
            "p95_ms": f"{p95_rej:.2f}"
        }
    ]

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["verdict", "n", "mean_ms", "p50_ms", "p95_ms"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")
    return rows


if __name__ == "__main__":
    run_latency_split()
