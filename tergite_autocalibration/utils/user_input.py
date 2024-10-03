# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


from ..lib.utils.samplespace import resonator_samples

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
qubits = ["q06", "q07", "q08", "q09", "q10", "q11", "q12", "q13", "q14", "q15"]
user_samplespace = {
    "resonator_spectroscopy": {
        "ro_frequencies": {qubit: resonator_samples(qubit) for qubit in qubits}
    },
}

####################################################################

"""
The dictionary user_requested_calibration
is what we pass to the calibration supervisor
"""
user_requested_calibration = {
    "user_samplespace": user_samplespace,
}
