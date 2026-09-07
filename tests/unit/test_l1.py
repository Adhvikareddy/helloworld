from src.qds.teleportation_qds import TeleportationQDS

def test_l1_core():
    qds = TeleportationQDS(seed=42)
    res = qds.execute_verification(shots=10)
    assert res["protocol_valid"]
    assert "basis_probabilities" in res
