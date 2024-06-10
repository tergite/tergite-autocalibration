qubits = [ 'q16','q18','q19','q20','q21','q22','q23','q24','q25']
# qubits = ['q21','q22','q23','q24','q25']
# qubits = ['q18','q19']
# qubits = ['q23','q24']
# couplers = ['q12_q13','q13_q14' ]
couplers = ['q22_q23']
# couplers = ['q23_q24']
# couplers = ['q19_q20']
# couplers = ['q18_q19']

attenuation_setting = {'qubit':12, 'coupler':30, 'readout':6}

'''
node reference
  punchout
  resonator_spectroscopy
  qubit_01_spectroscopy
  qubit_01_spectroscopy_pulsed
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
  check_cliffords
  cz_chevron
  cz_chevron_amplitude
  cz_optimize_chevron
  reset_chevron
  reset_calibration_ssro
  cz_calibration
  cz_calibration_ssro
  cz_dynamic_phase
  cz_dynamic_phase_swap
  tqg_randomized_benchmarking
  tqg_randomized_benchmarking_interleaved
'''

user_requested_calibration = {
    'target_node': 'reset_calibration_ssro',
    'all_qubits': qubits,
    'couplers': couplers,
}
