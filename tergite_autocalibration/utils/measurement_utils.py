# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


def reduce_samplespace(iteration: int, samplespace: dict) -> dict:
    reduced_samplespace = {}
    element_values = {}

    """
    example of external_samplespace:
    external_samplespace = {
          'cw_frequencies': {
             'q1': np.array(4.0e9, 4.1e9, 4.2e9),
             'q2': np.array(4.5e9, 4.6e9, 4.7e9),
           }
    }
    """
    # e.g. 'cw_frequencies':
    external_settable = list(samplespace.keys())[0]

    # elements may refer to qubits or couplers
    elements = samplespace[external_settable].keys()
    for element in elements:
        qubit_specific_values = samplespace[external_settable][element]
        current_value = qubit_specific_values[iteration]
        element_values[element] = current_value

    """
    example of reduced_external_samplespace:
    reduced_external_samplespace = {
        'cw_frequencies': {
             'q1': np.array(4.2e9),
             'q2': np.array(4.7e9),
        }
    }
    """
    reduced_samplespace[external_settable] = element_values
    return reduced_samplespace
