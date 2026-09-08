"""
Q-SENTINEL Noise Model.

Generates Qiskit-Aer noise models based on disturbance probability.
Models depolarizing errors in the quantum transmission channel and readout errors.
"""
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError

def get_noise_model(disturbance_prob: float) -> NoiseModel:
    """
    Generate a configurable noise model for channel transmission.
    
    Args:
        disturbance_prob: The base probability of error (0.0 to 1.0).
            0.0 = clean execution (ideal simulator).
            >0.0 = applies depolarizing errors to channel transmission.
            
    Returns:
        A Qiskit Aer NoiseModel.
    """
    noise_model = NoiseModel()
    
    if disturbance_prob <= 0.0:
        return noise_model
        
    dist = min(1.0, disturbance_prob)
    
    # Depolarizing error on channel transmission (qubit 2)
    p_depol = dist * 0.75
    depol_error = depolarizing_error(p_depol, 1)
    noise_model.add_quantum_error(depol_error, ['h', 'x', 'z', 's', 'sdg', 'id'], [2])
    
    # Readout Error on Bob's measurement
    p_ro = min(0.5, dist * 0.25)
    ro_error = ReadoutError([[1 - p_ro, p_ro], [p_ro, 1 - p_ro]])
    noise_model.add_readout_error(ro_error, [2])
    
    return noise_model

