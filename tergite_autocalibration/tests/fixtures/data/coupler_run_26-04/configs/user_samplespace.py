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

user_samplespace = {}
####################################################################
# import numpy as np
#
# from tergite_autocalibration.config.legacy import dh
#
#
# def qubit_samples(qubit: str, transition: str = "01") -> np.ndarray:
#     qub_spec_samples = 301
#     sweep_range = 28e6
#     if transition == "01":
#         VNA_frequency = dh.get_legacy("VNA_qubit_frequencies")[qubit]
#     elif transition == "12":
#         VNA_frequency = dh.get_legacy("VNA_f12_frequencies")[qubit]
#     # FIXME: This is not safe, because VNA_frequency might be undefined
#     min_freq = VNA_frequency - sweep_range / 2
#     max_freq = VNA_frequency + sweep_range / 2
#     return np.linspace(min_freq, max_freq, qub_spec_samples)
#
#
# qubits = ["q13", "q14", "q15"]
# couplers = ["q13_q14"]
#
# user_samplespace = {
#     "qubit_12_spectroscopy": {
#         "spec_pulse_amplitudes": {
#             qubit: np.linspace(4e-3, 4e-2, 4) for qubit in qubits
#         },
#         "spec_frequencies": {
#             qubit: qubit_samples(qubit, transition="12") for qubit in qubits
#         },
#     }
# }
# ####################################################################
