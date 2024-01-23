# qubits = [ 'q16','q17','q18','q19','q20','q21','q22','q23','q24','q25']
# qubits = [ 'q18','q19','q20','q21','q22','q23','q24','q25']
qubits = ['q12','q13','q14','q15']
# couplers = ['q12_q13','q13_q14' ]
couplers = ['q12_q13', 'q14_q15']

'''
node reference
  punchout
  resonator_spectroscopy
  qubit_01_spectroscopy_multidim
  qubit_01_spectroscopy_pulsed
  qubit_12_spectroscopy_multidim
  rabi_oscillations
  ramsey_correction
  resonator_spectroscopy_1
  qubit_12_spectroscopy_pulsed
  rabi_oscillations_12
  resonator_spectroscopy_2
  coupler_spectroscopy
  coupler_resonator_spectroscopy
  motzoi_parameter
  n_rabi_oscillations
  T1
  cz_chevron
  cz_calibration
'''

user_requested_calibration = {
    'target_node': 'rabi_oscillations',
    'all_qubits': qubits,
    'couplers': couplers,
}
