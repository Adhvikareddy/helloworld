"""
Channel Manipulation Attack — L2 statistical detector test.

The attacker introduces a controlled disturbance BEFORE measurement via
a parameterised quantum-channel perturbation (rx/rz rotations injected
into the teleportation circuit).  Fresh Qiskit-Aer shots are executed;
the resulting X/Y/Z distributions are passed through the normal L2
detector; the frozen threshold policy decides ACCEPT/QUARANTINE/REJECT.

The decision is NEVER forced by the attacker.

Disturbance levels:
  low    = 0.10 (subtle phase/bit perturbation)
  medium = 0.25 (moderate channel degradation)
  high   = 0.50 (strong channel corruption)
"""
import uuid
import datetime
from attacker.client import get_base_payload, send_verify
from attacker.reporting import make_attack_result, print_result, aggregate_results
from attacker.config import DISTURBANCE_LEVELS, DEFAULT_SHOTS


def run_channel(
    levels: list = None,
    shots: int = DEFAULT_SHOTS,
    repeats: int = 3,
) -> list:
    """
    Execute channel manipulation at multiple disturbance levels.

    For each (level, repeat):
      1. Construct a legitimate verification request.
      2. Set disturbance_prob to the documented numerical value.
      3. Submit — the API injects rx/rz perturbations into the Qiskit
         circuit BEFORE measurement and executes fresh shots.
      4. Collect the actual X/Y/Z measurement distributions, D, χ²,
         and the decision.
      5. Record all measured values — do NOT fabricate or force.
    """
    if levels is None:
        levels = list(DISTURBANCE_LEVELS.keys())

    results = []
    run_id = f"channel-{uuid.uuid4()}"

    for level_name in levels:
        disturbance = DISTURBANCE_LEVELS.get(level_name, float(level_name))
        for rep in range(repeats):
            started = datetime.datetime.utcnow().isoformat()
            payload = get_base_payload(
                shots=shots,
                experiment_id=f"channel_{level_name}_{rep}",
            )
            payload["disturbance_prob"] = disturbance

            raw = send_verify(payload)
            resp = raw["response"]

            if raw["http_status"] == 403:
                actual_decision = "REJECT"
                reason = resp.get("detail", "")
            else:
                actual_decision = resp.get("decision", "ERROR")
                reason = resp.get("reason", "")

            results.append(make_attack_result(
                attack_type="channel_manipulation",
                target="/v1/qds/verify",
                expected_primary_layer="L2",
                expected_outcome="QUARANTINE/REJECT",
                actual_outcome=actual_decision,
                detected=actual_decision != "ACCEPT",
                event_id=resp.get("evidence_id"),
                reason=reason,
                parameters={
                    "disturbance_level": level_name,
                    "disturbance_prob": disturbance,
                    "shots": shots,
                    "repeat": rep,
                },
                measurements={
                    "deviation_score": resp.get("deviation_score"),
                    "chi_square": resp.get("chi_square"),
                    "threshold_low": resp.get("threshold_low"),
                    "threshold_high": resp.get("threshold_high"),
                    "shot_count": resp.get("shot_count"),
                    "latency_ms": resp.get("latency_ms"),
                },
                error=raw["error"],
                run_id=run_id,
                started_at=started,
                completed_at=raw["completed_at"],
            ))

    return results


if __name__ == "__main__":
    results = run_channel()
    for r in results:
        print_result(r)
    print("\nAggregate:", aggregate_results(results))
