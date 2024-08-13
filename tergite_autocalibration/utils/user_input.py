"""
node reference
  punchout
  resonator_spectroscopy
  qubit_01_spectroscopy
  qubit_01_spectroscopy_pulsed
  qubit_01_cw_spectroscopy
  rabi_oscillations
  ramsey_correction
  resonator_spectroscopy_1
  qubit_12_spectroscopy_pulsed
  qubit_12_spectroscopy_multidim
  rabi_oscillations_12
  ramsey_correction_12
  resonator_spectroscopy_2
  ro_frequency_two_state_optimization
  ro_frequency_three_state_optimization
  ro_amplitude_two_state_optimization
  ro_amplitude_three_state_optimization
  coupler_spectroscopy
  coupler_resonator_spectroscopy
  motzoi_parameter
  n_rabi_oscillations
  randomized_benchmarking
  state_discrimination
  T1
  T2
  T2_echo
  randomized_benchmarking
  all_XY
  check_cliffords
  cz_chevron
  cz_chevron_test
  cz_chevron_amplitude
  cz_optimize_chevron
  reset_chevron
  reset_calibration_ssro
  cz_calibration
  cz_calibration_ssro
  cz_dynamic_phase
  cz_dynamic_phase_swap
  process_tomography_ssro
  tqg_randomized_benchmarking
  tqg_randomized_benchmarking_interleaved
"""

import numpy as np

from tergite_autocalibration.config.VNA_values import (
    VNA_f12_frequencies,
    VNA_qubit_frequencies,
    VNA_resonator_frequencies,
)


def resonator_samples(qubit: str) -> np.ndarray:
    res_spec_samples = 101
    sweep_range = 4.0e6
    VNA_frequency = VNA_resonator_frequencies[qubit]
    min_freq = VNA_frequency - sweep_range / 2 - 0.5e6
    max_freq = VNA_frequency + sweep_range / 2
    return np.linspace(min_freq, max_freq, res_spec_samples)


def qubit_samples(qubit: str, transition: str = "01") -> np.ndarray:
    qub_spec_samples = 51
    sweep_range = 10e6
    if transition == "01":
        VNA_frequency = VNA_qubit_frequencies[qubit]
    elif transition == "12":
        VNA_frequency = VNA_f12_frequencies[qubit]
    min_freq = VNA_frequency - sweep_range / 2
    max_freq = VNA_frequency + sweep_range / 2
    return np.linspace(min_freq, max_freq, qub_spec_samples)


"""
user_samplespace schema:
user_samplespace = {
    node1_name : {
            "settable_of_node1_1": { 'q1': np.ndarray, 'q2': np.ndarray },
            "settable_of_node1_2": { 'q1': np.ndarray, 'q2': np.ndarray },
            ...
        },
    node2_name : {
            "settable_of_node2_1": { 'q1': np.ndarray, 'q2': np.ndarray },
            "settable_of_node2_2": { 'q1': np.ndarray, 'q2': np.ndarray },
            ...
        }
}
"""
####################################################################
target_node = "reset_chevron"
qubits = ["q16", "q17", "q18", "q19", "q20", "q21", "q22", "q23", "q24", "q25"]
couplers = ["q23_q24"]
user_samplespace = {
    "resonator_spectroscopy": {
        "ro_frequencies": {qubit: resonator_samples(qubit) for qubit in qubits}
    },
}
attenuation_setting = {"qubit": 12, "coupler": 30, "readout": 6}

####################################################################

"""
The dictionary user_requested_calibration
is what we pass to the calibration supervisor
"""
user_requested_calibration = {
    "target_node": target_node,
    "all_qubits": qubits,
    "couplers": couplers,
    "user_samplespace": user_samplespace,
}
