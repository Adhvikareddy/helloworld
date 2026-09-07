"""
Attack result reporting utilities.

Every attack produces a structured JSON result conforming to the contract
defined in the Q-SENTINEL specification.
"""
import uuid
import datetime
import json
from typing import Optional


def make_attack_result(
    attack_type: str,
    target: str,
    expected_primary_layer: str,
    expected_outcome: str,
    actual_outcome: str,
    detected: bool,
    event_id: Optional[str] = None,
    reason: Optional[str] = None,
    evidence_hash: Optional[str] = None,
    parameters: Optional[dict] = None,
    measurements: Optional[dict] = None,
    error: Optional[str] = None,
    run_id: Optional[str] = None,
    attack_id: Optional[str] = None,
    started_at: Optional[str] = None,
    completed_at: Optional[str] = None,
) -> dict:
    """
    Create a structured attack result conforming to the Q-SENTINEL spec.
    """
    return {
        "run_id": run_id or f"run-{uuid.uuid4()}",
        "attack_id": attack_id or f"atk-{uuid.uuid4()}",
        "attack_type": attack_type,
        "target": target,
        "started_at": started_at or datetime.datetime.utcnow().isoformat(),
        "completed_at": completed_at or datetime.datetime.utcnow().isoformat(),
        "expected_primary_layer": expected_primary_layer,
        "expected_outcome": expected_outcome,
        "actual_outcome": actual_outcome,
        "detected": detected,
        "event_id": event_id,
        "reason": reason,
        "evidence_hash": evidence_hash,
        "parameters": parameters or {},
        "measurements": measurements or {},
        "error": error,
    }


def print_result(result: dict) -> None:
    """Pretty-print an attack result."""
    print(json.dumps(result, indent=2, default=str))


def aggregate_results(results: list) -> dict:
    """Compute aggregate statistics over a list of attack results."""
    total = len(results)
    detected = sum(1 for r in results if r["detected"])
    errors = sum(1 for r in results if r["error"] is not None)
    return {
        "total_attempts": total,
        "detected": detected,
        "not_detected": total - detected - errors,
        "errors": errors,
        "detection_rate": detected / total if total > 0 else 0.0,
    }
