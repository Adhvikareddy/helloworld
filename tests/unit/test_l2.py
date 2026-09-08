"""
L2 — Statistical Threat Detector Tests.

These tests verify that the deviation D, chi-square, and decision policy
work correctly with real computed values.
"""
import pytest
import os
import json
from src.detection.statistics import DetectorStatistics
from src.detection.policy import DecisionPolicy
from src.detection.baseline import BaselineManager


class TestDeviation:
    """Verify deviation D computation."""

    def test_zero_deviation_for_exact_match(self):
        mu = {"X": {"0": 1.0, "1": 0.0}, "Y": {"0": 0.5, "1": 0.5}}
        p_hat = {"X": {"0": 1.0, "1": 0.0}, "Y": {"0": 0.5, "1": 0.5}}
        D = DetectorStatistics.compute_deviation(p_hat, mu)
        assert D == 0.0

    def test_nonzero_deviation_for_mismatch(self):
        mu = {"X": {"0": 1.0, "1": 0.0}}
        p_hat = {"X": {"0": 0.8, "1": 0.2}}
        D = DetectorStatistics.compute_deviation(p_hat, mu)
        assert D > 0
        assert abs(D - 0.08) < 0.001  # (0.2)^2 + (0.2)^2 = 0.08

    def test_deviation_increases_with_disturbance(self):
        mu = {"X": {"0": 1.0, "1": 0.0}, "Y": {"0": 0.5, "1": 0.5}, "Z": {"0": 0.5, "1": 0.5}}
        p_small = {"X": {"0": 0.95, "1": 0.05}, "Y": {"0": 0.5, "1": 0.5}, "Z": {"0": 0.5, "1": 0.5}}
        p_large = {"X": {"0": 0.7, "1": 0.3}, "Y": {"0": 0.6, "1": 0.4}, "Z": {"0": 0.4, "1": 0.6}}

        D_small = DetectorStatistics.compute_deviation(p_small, mu)
        D_large = DetectorStatistics.compute_deviation(p_large, mu)
        assert D_large > D_small

    def test_weighted_deviation(self):
        mu = {"X": {"0": 1.0, "1": 0.0}}
        p_hat = {"X": {"0": 0.8, "1": 0.2}}
        weights = {"X": {"0": 2.0, "1": 2.0}}
        D = DetectorStatistics.compute_deviation(p_hat, mu, weights=weights)
        # 2*(0.2)^2 + 2*(0.2)^2 = 0.16
        assert abs(D - 0.16) < 0.001


class TestChiSquare:
    """Verify chi-square computation."""

    def test_zero_chi_square_for_exact_match(self):
        mu = {"X": {"0": 0.5, "1": 0.5}}
        p_hat = {"X": {"0": 0.5, "1": 0.5}}
        chi2 = DetectorStatistics.compute_chi_square(p_hat, mu, N=1024)
        assert chi2 == 0.0

    def test_chi_square_scales_with_shots(self):
        mu = {"X": {"0": 1.0, "1": 0.0}}
        p_hat = {"X": {"0": 0.9, "1": 0.1}}
        chi2_100 = DetectorStatistics.compute_chi_square(p_hat, mu, N=100)
        chi2_1000 = DetectorStatistics.compute_chi_square(p_hat, mu, N=1000)
        assert chi2_1000 > chi2_100

    def test_chi_square_epsilon_prevents_division_by_zero(self):
        mu = {"X": {"0": 0.0, "1": 1.0}}  # mu=0 would cause division by zero
        p_hat = {"X": {"0": 0.1, "1": 0.9}}
        chi2 = DetectorStatistics.compute_chi_square(p_hat, mu, N=100, epsilon=1e-4)
        assert chi2 > 0  # Should not crash


class TestDecisionPolicy:
    """Verify ACCEPT/QUARANTINE/REJECT decision boundaries."""

    def setup_method(self):
        self.filepath = "data/test_thresholds_l2.json"
        self.policy = DecisionPolicy(filepath=self.filepath)
        self.policy.save_thresholds(0.05, 0.15, "test-v1")

    def teardown_method(self):
        if os.path.exists(self.filepath):
            os.remove(self.filepath)

    def test_accept_below_tau_low(self):
        assert self.policy.evaluate(0.02) == "ACCEPT"
        assert self.policy.evaluate(0.0) == "ACCEPT"
        assert self.policy.evaluate(0.05) == "ACCEPT"

    def test_quarantine_between_thresholds(self):
        assert self.policy.evaluate(0.06) == "QUARANTINE"
        assert self.policy.evaluate(0.10) == "QUARANTINE"
        assert self.policy.evaluate(0.15) == "QUARANTINE"

    def test_reject_above_tau_high(self):
        assert self.policy.evaluate(0.16) == "REJECT"
        assert self.policy.evaluate(1.0) == "REJECT"

    def test_version_tracking(self):
        assert self.policy.get_version() == "test-v1"


class TestBaselineManager:
    """Verify baseline load/save."""

    def setup_method(self):
        self.filepath = "data/test_baseline_l2.json"

    def teardown_method(self):
        if os.path.exists(self.filepath):
            os.remove(self.filepath)

    def test_uncalibrated_fallback(self):
        mgr = BaselineManager(filepath="data/nonexistent.json")
        assert mgr.get_version() == "uncalibrated"
        mu = mgr.get_mu_dict()
        assert "X" in mu and "Y" in mu and "Z" in mu

    def test_save_and_load(self):
        mgr = BaselineManager(filepath=self.filepath)
        mu = {"X": {"0": 0.99, "1": 0.01}, "Y": {"0": 0.5, "1": 0.5}, "Z": {"0": 0.5, "1": 0.5}}
        sigma = {"X": {"0": 0.01, "1": 0.01}, "Y": {"0": 0.02, "1": 0.02}, "Z": {"0": 0.02, "1": 0.02}}
        mgr.save_baseline(mu, sigma, "test-calibrated")

        mgr2 = BaselineManager(filepath=self.filepath)
        assert mgr2.get_version() == "test-calibrated"
        loaded_mu = mgr2.get_mu_dict()
        assert abs(loaded_mu["X"]["0"] - 0.99) < 0.001
