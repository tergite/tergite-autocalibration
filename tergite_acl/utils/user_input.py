'''
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
  cz_optimize_chevron
  reset_chevron
  cz_calibration
  cz_calibration_ssro
  cz_dynamic_phase
'''

qubits = [ 'q06','q07','q08','q09','q10']
couplers = ['q12_q13']

'''
user_samplespace schema:
user_samplespace = {
    node1_name : {
            "settable_of_node1_1": np.ndarray,
            "settable_of_node1_2": np.ndarray,
            ...
        },
    node2_name : {
            "settable_of_node2_1": np.ndarray,
            "settable_of_node2_2": np.ndarray,
            ...
        }
}
'''

user_samplespace = {

}

'''
The dictionary user_requested_calibration
is what we pass to the calibration supervisor
'''
user_requested_calibration = {
    'target_node': 'all_XY',
    'all_qubits': qubits,
    'couplers': couplers,
    'user_samplespace': user_samplespace
}
