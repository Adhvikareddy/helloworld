"""
Calibration Tests.

These tests verify that the calibration pipeline uses actual Qiskit
measurements and produces sensible thresholds.
"""
import pytest
from src.calibration.grid_search import compute_baseline, collect_deviation_scores, grid_search_thresholds
from src.qds.teleportation_qds import TeleportationQDS


class TestCalibrationBaseline:
    """Verify baseline computation from actual Qiskit runs."""

    def test_baseline_has_all_bases(self):
        qds = TeleportationQDS(seed=42)
        mu, sigma = compute_baseline(qds, runs=5, shots=256)
        assert set(mu.keys()) == {"X", "Y", "Z"}
        assert set(sigma.keys()) == {"X", "Y", "Z"}

    def test_baseline_probabilities_valid(self):
        qds = TeleportationQDS(seed=42)
        mu, sigma = compute_baseline(qds, runs=5, shots=256)
        for basis in ["X", "Y", "Z"]:
            p0 = mu[basis]["0"]
            p1 = mu[basis]["1"]
            assert 0.0 <= p0 <= 1.0
            assert 0.0 <= p1 <= 1.0
            assert abs(p0 + p1 - 1.0) < 0.05  # Allow finite-shot noise

    def test_x_baseline_near_deterministic(self):
        """For |+⟩ state, X-basis should yield P(0) ≈ 1.0."""
        qds = TeleportationQDS(seed=42)
        mu, sigma = compute_baseline(qds, runs=10, shots=1024)
        assert mu["X"]["0"] > 0.90


class TestDeviationScores:
    """Verify adversarial deviation collection."""

    def test_higher_disturbance_gives_higher_scores(self):
        qds = TeleportationQDS(seed=42)
        mu, _ = compute_baseline(qds, runs=5, shots=256)
        scores = collect_deviation_scores(
            qds, mu, [0.10, 0.50], runs_per_level=5, shots=256
        )
        avg_low = sum(scores[0.10]) / len(scores[0.10])
        avg_high = sum(scores[0.50]) / len(scores[0.50])
        assert avg_high > avg_low


class TestThresholdSearch:
    """Verify grid search produces sensible thresholds."""

    def test_thresholds_ordered(self):
        leg = [0.001, 0.002, 0.003, 0.004, 0.005]
        adv = {0.10: [0.05, 0.06, 0.07], 0.25: [0.15, 0.20, 0.25]}
        tau_low, tau_high = grid_search_thresholds(leg, adv)
        assert tau_low < tau_high
        assert tau_low > max(leg)

    def test_thresholds_separate_populations(self):
        leg = [0.001, 0.002, 0.003]
        adv = {0.10: [0.10, 0.12, 0.15], 0.25: [0.20, 0.25, 0.30]}
        tau_low, tau_high = grid_search_thresholds(leg, adv)
        # All legitimate should be below tau_low
        for d in leg:
            assert d < tau_low
