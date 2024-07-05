all_qubits = ["q06", "q07", "q08", "q09", "q10"]

coupler_spi_map = {
    "q06_q07": (3, "dac1"),
    "q07_q08": (4, "dac0"),
    "q08_q09": (2, "dac0"),
    "q09_q10": (3, "dac2"),
}

edge_group = {
    "q11_q12": 1,
    "q12_q13": 2,
    "q13_q14": 1,
    "q14_q15": 2,
    "q11_q16": 3,
    "q12_q17": 4,
    "q13_q18": 3,
    "q14_q19": 4,
    "q15_q20": 3,
    "q16_q17": 2,
    "q17_q18": 1,
    "q18_q19": 2,
    "q19_q20": 1,
    "q16_q21": 4,
    "q17_q22": 3,
    "q18_q23": 4,
    "q19_q24": 3,
    "q20_q25": 4,
    "q21_q22": 1,
    "q22_q23": 2,
    "q23_q24": 1,
    "q24_q25": 2,
}

qubit_types = {}
for qubit in all_qubits:
    if int(qubit[1:]) % 2 == 0:
        # Even qubits are data/control qubits
        qubit_type = "Control"
    else:
        # Odd qubits are ancilla/target qubits
        qubit_type = "Target"
    qubit_types[qubit] = qubit_type
