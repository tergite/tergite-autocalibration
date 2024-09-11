# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
# (C) Amr Osman 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

all_qubits = [
    "q06",
    "q07",
    "q08",
    "q09",
    "q10",
    "q11",
    "q12",
    "q13",
    "q14",
    "q15",
    "q16",
    "q17",
    "q18",
    "q19",
    "q20",
    "q21",
    "q22",
    "q23",
    "q24",
    "q25",
]

coupler_spi_map = {
    #SPI A
    'q11_q12': (1, 'dac0'),
    'q12_q13': (1, 'dac1'),
    'q13_q14': (1, 'dac2'),
    'q14_q15': (1, 'dac3'),
    'q08_q09': (2, 'dac0'),
    'q12_q17': (2, 'dac1'),
    'q07_q12': (2, 'dac2'),
    'q08_q13': (2, 'dac3'),
    'q09_q14': (3, 'dac0'),
    'q06_q07': (3, 'dac1'),
    'q09_q10': (3, 'dac2'),
    'q11_q16': (3, 'dac3'),
    'q07_q08': (4, 'dac0'),
    'q10_q15': (4, 'dac1'),
    'q06_q11': (4, 'dac2'),
    # SPI B
    "q16_q17": (1, "dac0"),
    "q17_q18": (1, "dac1"),
    "q18_q19": (1, "dac2"),
    "q19_q20": (1, "dac3"),
    "q18_q23": (2, "dac0"),
    "q17_q22": (2, "dac1"),
    "q16_q21": (2, "dac2"),
    "q19_q24": (2, "dac3"),
    "q20_q25": (3, "dac0"),
    "q21_q22": (3, "dac1"),
    "q22_q23": (3, "dac2"),
    "q23_q24": (3, "dac3"),
    "q24_q25": (4, "dac0"),
    "q13_q18": (4, "dac1"),
    "q15_q20": (4, "dac2"),
    "q14_q19": (4, "dac3"),
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
