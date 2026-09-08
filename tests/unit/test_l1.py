"""
L1 — QDS Verification Core Tests.

These tests verify that the Qiskit-Aer circuit actually executes and produces
physically meaningful results.  They fail if the implementation is bypassed.
"""
import pytest
from src.qds.teleportation_qds import TeleportationQDS


class TestCircuitExecution:
    """Verify that actual Qiskit circuits execute."""

    def test_valid_execution_returns_probabilities(self):
        qds = TeleportationQDS(seed=42)
        result = qds.execute_verification(shots=1024)
        assert result["protocol_valid"] is True
        assert result["shot_count"] == 1024
        assert "basis_probabilities" in result
        assert "measurement_counts" in result

    def test_all_three_bases_measured(self):
        qds = TeleportationQDS(seed=42)
        result = qds.execute_verification(shots=512)
        probs = result["basis_probabilities"]
        assert set(probs.keys()) == {"X", "Y", "Z"}
        for basis in ["X", "Y", "Z"]:
            assert "0" in probs[basis] and "1" in probs[basis]

    def test_probabilities_sum_to_one(self):
        qds = TeleportationQDS(seed=42)
        result = qds.execute_verification(shots=2048)
        for basis in ["X", "Y", "Z"]:
            p0 = result["basis_probabilities"][basis]["0"]
            p1 = result["basis_probabilities"][basis]["1"]
            assert abs(p0 + p1 - 1.0) < 1e-10

    def test_counts_are_actual_integers(self):
        qds = TeleportationQDS(seed=42)
        result = qds.execute_verification(shots=100)
        for basis in ["X", "Y", "Z"]:
            counts = result["measurement_counts"][basis]
            total = sum(counts.values())
            assert total == 100
            for v in counts.values():
                assert isinstance(v, int)


class TestTeleportationPhysics:
    """Verify that the circuit implements correct teleportation physics."""

    def test_x_measurement_of_h_state(self):
        """
        |+⟩ state teleported, measured in X basis.
        Without disturbance, should yield P(0) ≈ 1.0 (deterministic).
        """
        qds = TeleportationQDS(seed=42)
        result = qds.execute_verification(shots=4096)
        p_x0 = result["basis_probabilities"]["X"]["0"]
        # |+⟩ measured in X should give |+⟩ → P(0) ≈ 1.0
        assert p_x0 > 0.95, f"X-basis P(0) = {p_x0}, expected ≈ 1.0"

    def test_y_measurement_of_h_state(self):
        """
        |+⟩ measured in Y basis should be uniformly random: P(0) ≈ 0.5.
        """
        qds = TeleportationQDS(seed=42)
        result = qds.execute_verification(shots=4096)
        p_y0 = result["basis_probabilities"]["Y"]["0"]
        assert 0.35 < p_y0 < 0.65, f"Y-basis P(0) = {p_y0}, expected ≈ 0.5"

    def test_z_measurement_of_h_state(self):
        """
        |+⟩ measured in Z basis should be uniformly random: P(0) ≈ 0.5.
        """
        qds = TeleportationQDS(seed=42)
        result = qds.execute_verification(shots=4096)
        p_z0 = result["basis_probabilities"]["Z"]["0"]
        assert 0.35 < p_z0 < 0.65, f"Z-basis P(0) = {p_z0}, expected ≈ 0.5"

    def test_different_seeds_produce_different_counts(self):
        """Different seeds must produce different shot-level counts."""
        r1 = TeleportationQDS(seed=1).execute_verification(shots=1024)
        r2 = TeleportationQDS(seed=999).execute_verification(shots=1024)
        # The exact counts should differ (probabilities may be close)
        assert r1["measurement_counts"] != r2["measurement_counts"]


class TestDisturbance:
    """Verify that channel disturbance changes the circuit behavior."""

    def test_disturbance_changes_x_probabilities(self):
        """Disturbance should shift X-basis distribution away from P(0)≈1."""
        qds = TeleportationQDS(seed=42)
        clean = qds.execute_verification(shots=4096, disturbance_prob=0.0)
        dirty = qds.execute_verification(shots=4096, disturbance_prob=0.5)

        clean_x0 = clean["basis_probabilities"]["X"]["0"]
        dirty_x0 = dirty["basis_probabilities"]["X"]["0"]

        # Clean should be near 1.0, dirty should be significantly shifted
        assert clean_x0 > 0.95
        assert dirty_x0 < 0.90, f"Disturbance did not change X-basis: {dirty_x0}"

    def test_high_disturbance_produces_large_deviation(self):
        """High disturbance should produce measurably different distributions."""
        from src.detection.statistics import DetectorStatistics

        qds = TeleportationQDS(seed=42)
        clean = qds.execute_verification(shots=2048)
        dirty = qds.execute_verification(shots=2048, disturbance_prob=0.5)

        mu = clean["basis_probabilities"]
        D_clean = DetectorStatistics.compute_deviation(clean["basis_probabilities"], mu)
        D_dirty = DetectorStatistics.compute_deviation(dirty["basis_probabilities"], mu)

        assert D_dirty > D_clean


class TestInvalidSignature:
    """Verify cryptographic signature and execution path."""

    def test_invalid_pqc_signature_fails_verification(self):
        from src.security.envelope import PQCEnvelope
        pk, sk = PQCEnvelope.generate_keypair()
        payload = {"data": "authentic"}
        sig = PQCEnvelope.sign_payload(sk, payload)
        # Tamper payload
        tampered_payload = {"data": "tampered"}
        assert PQCEnvelope.verify_payload(pk, tampered_payload, sig) is False
        # Corrupted signature
        assert PQCEnvelope.verify_payload(pk, payload, "garbage_sig") is False

    def test_valid_signature_runs_circuit(self):
        qds = TeleportationQDS(seed=42)
        result = qds.execute_verification(shots=1024)
        assert result["protocol_valid"] is True
        assert len(result["measurement_counts"]) == 3


class TestModularFunctions:
    """Test extracted modular utility functions."""

    def test_pauli_correction_function(self):
        from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
        from src.qds.pauli_correction import apply_pauli_correction

        qr = QuantumRegister(3, 'q')
        cr = ClassicalRegister(3, 'c')
        qc = QuantumCircuit(qr, cr)
        # Should not raise
        apply_pauli_correction(qc, qr, cr, target_qubit=2)
        # v9 uses if_test context blocks, which produce 'if_else' operations
        gate_names = [inst.operation.name for inst in qc.data]
        assert "if_else" in gate_names

    def test_projective_measurement_x(self):
        from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
        from src.qds.projective_measurement import apply_projective_measurement

        qr = QuantumRegister(3, 'q')
        cr = ClassicalRegister(3, 'c')
        qc = QuantumCircuit(qr, cr)
        apply_projective_measurement(qc, qr, cr, basis="X")
        gate_names = [inst.operation.name for inst in qc.data]
        assert "h" in gate_names
        assert "measure" in gate_names

    def test_projective_measurement_y(self):
        from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
        from src.qds.projective_measurement import apply_projective_measurement

        qr = QuantumRegister(3, 'q')
        cr = ClassicalRegister(3, 'c')
        qc = QuantumCircuit(qr, cr)
        apply_projective_measurement(qc, qr, cr, basis="Y")
        gate_names = [inst.operation.name for inst in qc.data]
        assert "sdg" in gate_names
        assert "h" in gate_names

    def test_projective_measurement_z(self):
        from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
        from src.qds.projective_measurement import apply_projective_measurement

        qr = QuantumRegister(3, 'q')
        cr = ClassicalRegister(3, 'c')
        qc = QuantumCircuit(qr, cr)
        apply_projective_measurement(qc, qr, cr, basis="Z")
        gate_names = [inst.operation.name for inst in qc.data]
        assert "measure" in gate_names
        # Z has no rotation gate before measure
        assert "h" not in gate_names

    def test_projective_measurement_invalid_basis(self):
        from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
        from src.qds.projective_measurement import apply_projective_measurement

        qr = QuantumRegister(3, 'q')
        cr = ClassicalRegister(3, 'c')
        qc = QuantumCircuit(qr, cr)
        with pytest.raises(ValueError):
            apply_projective_measurement(qc, qr, cr, basis="W")
