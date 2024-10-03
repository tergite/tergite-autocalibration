# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
# (C) Amr Osman 2024
# (C) Copyright Michele Faucci Giannelli 2024
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

qubit_types = {}
for qubit in all_qubits:
    if int(qubit[1:]) % 2 == 0:
        # Even qubits are data/control qubits
        qubit_type = "Control"
    else:
        # Odd qubits are ancilla/target qubits
        qubit_type = "Target"
    qubit_types[qubit] = qubit_type
