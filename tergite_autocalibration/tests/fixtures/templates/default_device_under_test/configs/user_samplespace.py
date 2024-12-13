# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Michele Faucci Giannelli 2024
# (C) Copyright Chalmers Next Labs AB 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# This is an example file on how to create a custom samplespace for your node.
import numpy as np

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
qubits = {"q00": 4.5e9, "q01": 4.9e9}


def resonator_samples(qubit: str) -> np.ndarray:
    res_spec_samples = 101
    sweep_range = 4.0e6
    vna_frequency = qubits[qubit]
    min_freq = vna_frequency - sweep_range / 2
    max_freq = vna_frequency + sweep_range / 2
    return np.linspace(min_freq, max_freq, res_spec_samples)


user_samplespace = {
    "resonator_spectroscopy": {
        "ro_frequencies": {qubit: resonator_samples(qubit) for qubit in qubits.keys()}
    },
}
####################################################################
