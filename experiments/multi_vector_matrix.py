"""
Q-SENTINEL Multi-Vector Matrix Experiment.

Tests every combination of attack vector and detector to produce a
detection matrix showing which detectors fire for which attacks.

Outputs a CSV matrix.
"""
import os
import csv
import uuid
import time
from src.qds.key_material import generate_key_set
from src.qds.teleportation_qds import TeleportationQDS
from src.keyvault import global_keyvault
from src.security.envelope import PQCEnvelope
from src.security.identity import global_pqc_identity
from src.security.nonce import global_nonce_guard, TimestampGuard
from src.detection.probes import AuthenticationProbe, FreshnessProbe, StatisticalProbe
from src.detection.correlation import CorrelationEngine
from src.detection.policy import global_policy


def _setup_identities():
    """Create test identities for the experiment."""
    alice_pk, alice_sk = PQCEnvelope.generate_keypair()
    mallory_pk, mallory_sk = PQCEnvelope.generate_keypair()

    global_pqc_identity.register_participant("alice_exp", alice_pk, is_verifier=False)
    global_pqc_identity.register_participant("bob_exp", alice_pk, is_verifier=True)
    global_pqc_identity.register_participant("mallory_exp", mallory_pk, is_verifier=False)

    return alice_sk, mallory_sk


def _run_scenario(name: str, alice_sk, mallory_sk, L: int = 100):
    """
    Run a single scenario end-to-end through all probes.
    Returns (decision, {detector_name: severity}).
    """
    session = global_keyvault.create_session("alice_exp", L)
    nonce = f"exp-{uuid.uuid4()}"

    payload = {
        "session_id": session.session_id,
        "signer_id": "alice_exp",
        "verifier_id": "bob_exp",
        "nonce": nonce,
        "timestamp": time.time(),
        "message_bit": 0,
        "measurement_bases": (["X", "Y", "Z"] * ((L // 3) + 1))[:L],
        "experiment_id": name,
    }

    # -- Scenario-specific mutations --
    signing_key = alice_sk
    disturbance = 0.0

    if name == "legitimate":
        pass  # Clean request
    elif name == "impersonation":
        signing_key = mallory_sk
    elif name == "replay":
        # Pre-register the nonce so it's seen as a replay
        global_nonce_guard.is_fresh(nonce, session.session_id)
    elif name == "stale_timestamp":
        payload["timestamp"] = time.time() - 3600
    elif name == "quantum_forgery":
        disturbance = 1.0
    elif name == "channel_manipulation":
        disturbance = 0.25
    elif name == "composite":
        signing_key = mallory_sk
        payload["timestamp"] = time.time() - 3600
        disturbance = 0.5

    # Sign
    sig = PQCEnvelope.sign_payload(signing_key, payload)

    # -- Run probes --
    all_findings = []

    # L3: Auth
    is_identity_valid = global_pqc_identity.verify_request_signature(
        payload["signer_id"], payload, sig
    )
    is_authorized = global_pqc_identity.is_verifier_authorized(payload["verifier_id"])
    all_findings.extend(AuthenticationProbe.evaluate(
        is_identity_valid, is_authorized,
        payload["signer_id"], payload["verifier_id"]
    ))

    # L3: Freshness
    is_ts_valid = TimestampGuard.is_valid(payload["timestamp"])
    is_fresh = global_nonce_guard.is_fresh(payload["nonce"], payload["session_id"])
    all_findings.extend(FreshnessProbe.evaluate(
        is_ts_valid, not is_fresh,
        payload["nonce"], payload["session_id"]
    ))

    # L1/L2: Quantum
    try:
        alice_keys = global_keyvault.reveal_keys(
            session.session_id, "alice_exp", payload["message_bit"]
        )
        qds = TeleportationQDS(disturbance_prob=disturbance)
        bob_outcomes, _ = qds.execute_session(
            alice_keys, payload["measurement_bases"],
            f"{session.session_id}:{nonce}"
        )
        tau_low, tau_high = global_policy.get_thresholds()
        all_findings.extend(StatisticalProbe.evaluate(
            alice_keys, payload["measurement_bases"], bob_outcomes,
            tau_low, tau_high
        ))
    except Exception as e:
        from src.detection.findings import Finding, Severity
        all_findings.append(Finding(
            detector_name="QuantumError",
            severity=Severity.REJECT,
            description=str(e),
            metrics={}
        ))

    # Correlate
    decision, serialized = CorrelationEngine.evaluate_findings(all_findings)

    # Build detector map
    detector_map = {}
    for f in serialized:
        detector_map[f["detector"]] = f["severity"]

    return decision, detector_map


def run_multi_vector_matrix(output_dir: str = "experiments/results"):
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "multi_vector_matrix.csv")

    alice_sk, mallory_sk = _setup_identities()

    scenarios = [
        "legitimate",
        "impersonation",
        "replay",
        "stale_timestamp",
        "quantum_forgery",
        "channel_manipulation",
        "composite",
    ]

    all_detectors = set()
    results = []

    for scenario in scenarios:
        decision, detector_map = _run_scenario(scenario, alice_sk, mallory_sk)
        results.append({
            "scenario": scenario,
            "decision": decision,
            **detector_map
        })
        all_detectors.update(detector_map.keys())

    # Print matrix
    all_detectors = sorted(all_detectors)
    header = ["scenario", "decision"] + all_detectors

    print("\n" + "=" * 80)
    print("  Q-SENTINEL Multi-Vector Detection Matrix")
    print("=" * 80)
    print(f"{'Scenario':<25} {'Decision':<12} " +
          " ".join(f"{d[:12]:<14}" for d in all_detectors))
    print("-" * 80)

    for r in results:
        row = f"{r['scenario']:<25} {r['decision']:<12} "
        for d in all_detectors:
            severity = r.get(d, "-")
            row += f"{severity:<14} "
        print(row)

    # Write CSV
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for r in results:
            row = {"scenario": r["scenario"], "decision": r["decision"]}
            for d in all_detectors:
                row[d] = r.get(d, "-")
            writer.writerow(row)

    print(f"\nResults saved to {output_path}")
    return results


if __name__ == "__main__":
    run_multi_vector_matrix()
