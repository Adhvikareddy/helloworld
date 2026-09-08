"""
Q-SENTINEL Noise Model.

Generates Qiskit-Aer noise models based on disturbance probability.
Models both depolarizing errors in the channel and readout errors.
"""
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError

def get_noise_model(disturbance_prob: float) -> NoiseModel:
    """
    Generate a configurable noise model.
    
    Args:
        disturbance_prob: The base probability of error (0.0 to 1.0).
            0.0 = clean execution (ideal simulator).
            >0.0 = applies depolarizing errors to channel qubits and readout errors.
            
    Returns:
        A Qiskit Aer NoiseModel.
    """
    noise_model = NoiseModel()
    
    if disturbance_prob <= 0.0:
        return noise_model
        
    # Cap disturbance to 1.0
    dist = min(1.0, disturbance_prob)
    
    # We apply depolarizing error to single qubit identity operations (representing idle transmission)
    # and readout errors proportional to the disturbance.
    
    # 1. Depolarizing Error on the channel
    # The teleported qubit undergoes some channel degradation.
    # We'll apply this error broadly to all 1-qubit gates for simplicity in the simulation,
    # or specifically to the transmission step if modeled.
    p_depol = dist * 0.75  # Scale down slightly so it's not immediately fully mixed at dist=0.5
    depol_error = depolarizing_error(p_depol, 1)
    
    # Apply to all 1-qubit gates (h, x, z, s, sdg, id)
    noise_model.add_all_qubit_quantum_error(depol_error, ['h', 'x', 'z', 's', 'sdg', 'id'])
    
    # 2. Readout Error
    # Probability of measuring 0 given 1, and 1 given 0
    p_ro = dist * 0.25
    p_ro = min(0.5, p_ro) # Max mixing is uniform
    
    ro_error = ReadoutError([[1 - p_ro, p_ro], [p_ro, 1 - p_ro]])
    noise_model.add_all_qubit_readout_error(ro_error)
    
    return noise_model
