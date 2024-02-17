all_qubits = ['q11', 'q12', 'q13', 'q14', 'q15', 'q16', 'q17', 'q18', 'q19', 'q20','q21','q22','q23','q24','q25']

coupler_spi_map = {
    # 'q11_q12': (1, 'dac0'),
    # 'q12_q13': (1, 'dac1'),
    'q13_q14': (1, 'dac2'),
    # 'q14_q15': (1, 'dac3'),
    # 'q16_q17': (1, 'dac0'), # slightly heating?
    # 'q17_q18': (1, 'dac1'),
    # 'q18_q19': (1, 'dac2'),
    # 'q19_q20': (1, 'dac3'), # slightly heating? , possibly +0.5mK for a coupler spectroscopy round
    # 'q16_q21': (2, 'dac2'),
    # 'q17_q22': (2, 'dac1'),
    # 'q18_q23': (2, 'dac0'),
    # 'q21_q22': (3, 'dac1'),
    # 'q22_q23': (3, 'dac2'), # badly heating?
    # 'q23_q24': (3, 'dac3'),
    # 'q20_q25': (3, 'dac0'),
    # 'q24_q25': (4, 'dac0'),
}

edge_group = {'q11_q12':1,'q12_q13':2,'q13_q14':1,'q14_q15':2,
        'q11_q16':3,'q12_q17':4,'q13_q18':3,'q14_q19':4,'q15_q20':3,
        'q16_q17':2,'q17_q18':1,'q18_q19':2,'q19_q20':1,
        'q16_q21':4,'q17_q22':3,'q18_q23':4,'q19_q24':3,'q20_q25':4,
        'q21_q22':1,'q22_q23':2,'q23_q24':1,'q24_q25':2}

qubit_types = {}
for qubit in all_qubits:
    if int(qubit[1:]) % 2 == 0:
        # Even qubits are data/control qubits
        qubit_type = 'Control'
    else:
        # Odd qubits are ancilla/target qubits
        qubit_type = 'Target'
    qubit_types[qubit] = qubit_type
