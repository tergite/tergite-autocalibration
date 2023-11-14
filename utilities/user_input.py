qubits = [ 'q16','q17','q18','q19','q20','q21','q22','q23','q24','q25']
#qubits = ['q16', 'q17', 'q19', 'q21', 'q22', 'q23', 'q25']
#qubits = [ 'q22','q23', 'q25']

'''
node reference
  punchout
  resonator_spectroscopy
  qubit_01_spectroscopy_multidim
  qubit_01_spectroscopy_pulsed
  rabi_oscillations
  ramsey_correction
  resonator_spectroscopy_1
  qubit_12_spectroscopy_pulsed
  rabi_oscillations_12
  resonator_spectroscopy_2
  coupler_spectroscopy
  coupler_resonator_spectroscopy
  T1
  cz_chevron
'''

user_requested_calibration = {
    'target_node': 'qubit_01_spectroscopy_pulsed',
    'all_qubits': qubits,
    'node_dictionary' : {'coupled_qubits': ['q21','q22']},
}
        # 'cz_chevron': {
        #     'cz_pulse_frequencies_sweep': {qubit: np.linspace(-50e6,50e6,5) for qubit in qubits},
        #     'cz_pulse_amplitudes': {qubit: np.linspace(0.0,0.001,7) for qubit in qubits},
        #     # 'cz_pulse_duration': {qubit: 200e-9 for qubit in qubits},
        #     # 'cz_pulse_width': {qubit: 4e-9 for qubit in qubits},
        # }
