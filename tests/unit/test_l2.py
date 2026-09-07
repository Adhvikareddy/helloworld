from src.detection.statistics import DetectorStatistics
from src.detection.policy import DecisionPolicy

def test_deviation():
    mu = {"X": {"0": 1.0}}
    p_hat = {"X": {"0": 0.8}}
    D = DetectorStatistics.compute_deviation(p_hat, mu)
    assert round(D, 2) == 0.04

def test_policy():
    policy = DecisionPolicy(filepath="data/test_thresh.json")
    policy.save_thresholds(0.05, 0.15, "v1")
    assert policy.evaluate(0.02) == "ACCEPT"
    assert policy.evaluate(0.10) == "QUARANTINE"
    assert policy.evaluate(0.20) == "REJECT"
