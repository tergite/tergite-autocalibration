#qubits = [ 'q16','q17','q18','q19','q20','q21','q22','q23','q24','q25']
#qubits = ['q10','q13','q15']
#qubits = [ 'q06']
qubits = [ 'q06','q07', 'q08', 'q09', 'q10','q11','q12','q13', 'q14', 'q15']

# qubits = [ 'q18','q19','q20','q21','q22','q23','q24','q25']
#qubits = ['q12','q13','q14']
# qubits = ['q14']
# couplers = ['q12_q13','q13_q14' ]
#couplers = ['q16_q21']

# coupler_spi_map = {
#     # SPI A
#     'q11_q12': (1, 'dac0'),
#     'q12_q13': (1, 'dac1'),
#     'q13_q14': (1, 'dac2'),
#     'q14_q15': (1, 'dac3'),
#     'q08_q09': (2, 'dac0'),
#     'q12_q17': (2, 'dac1'),
#     'q07_q12': (2, 'dac2'),
#     'q08_q13': (2, 'dac3'),
#     'q09_q14': (3, 'dac0'),
#     'q06_q07': (3, 'dac1'),
#     'q09_q10': (3, 'dac2'),
#     'q11_q16': (3, 'dac3'),
#     'q07_q08': (4, 'dac0'),
#     'q10_q15': (4, 'dac1'),
#     'q06_q11': (4, 'dac2'),

# }
#couplers = ['q11_q12'] # not tuning
#couplers = ['q12_q13'] #done
#couplers = ['q13_q14']
#couplers = ['q14_q15']
#couplers = ['q08_q09']
#couplers = ['q12_q17']
#couplers = ['q07_q12']
#couplers = ['q08_q13']
#couplers = ['q09_q14']
##couplers = ['q06_q07']
#couplers = ['q09_q10']
#couplers = ['q11_q16']
#couplers = ['q07_q08']
#couplers = ['q10_q15']
couplers = ['q06_q11']


attenuation_setting = {'qubit':12, 'coupler':40, 'readout':12}

'''punchout
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
  cz_optimize_chevron
  reset_chevron
  cz_calibration
  cz_calibration_ssro
  cz_dynamic_phase
'''

user_requested_calibration = {
    'target_node': 'randomized_benchmarking',
    'all_qubits': qubits,
    'couplers': couplers,
}
