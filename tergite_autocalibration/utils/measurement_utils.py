# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


from typing import Iterable

import numpy


def reduce_samplespace(iteration: int, samplespace: dict) -> dict:
    reduced_samplespace = {}
    element_values = {}

    # To account for empty samplespaces
    if not samplespace:
        return reduced_samplespace

    """
    example of samplespace:
    samplespace = {
          'frequencies': {
             'q1': np.array([4.0e9, 4.1e9, 4.2e9]),
             'q2': np.array([4.5e9, 4.6e9, 4.7e9]),
           }
    }
    """
    # e.g. 'frequencies':
    settable = list(samplespace.keys())[0]

    # elements may refer to qubits or couplers
    elements = samplespace[settable].keys()  # ['q1', 'q2'] in the example
    for element in elements:
        qubit_specific_values = samplespace[settable][element]
        current_value = qubit_specific_values[iteration]
        element_values[element] = current_value

    """
    example of reduced_samplespace at the 3rd iteration:
    reduced_external_samplespace = {
        'frequencies': {
             'q1': np.array(4.2e9),
             'q2': np.array(4.7e9),
        }
    }
    """
    reduced_samplespace[settable] = element_values
    return reduced_samplespace


def samplespace_dimensions(samplespace: dict, loops=None) -> list[int]:
    """
    example of a samplespace:
    samplespace = {
          'frequencies': {
             'q1': np.array([4.0e9, 4.1e9, 4.2e9]),
             'q2': np.array([4.5e9, 4.6e9, 4.7e9]),
           },
         'amplitudes': {
             'q1': np.array([0.1,0.2,0.3,0.4,0.5]),
             'q2': np.array([0.2,0.3,0.4,0.5,0.6]),
           }
    }
    the resulting dimensions are then [3,5]
    """
    dimensions = []
    settable_quantities = samplespace.keys()

    for quantity in settable_quantities:
        # keeping the first element, ASSUMING that all settable elements
        # have the same dimensions on their samplespace
        first_element = list(samplespace[quantity].keys())[0]  # 'q1' in the example
        # the array of frequencies or amplitudes in the example:
        settable_values = samplespace[quantity][first_element]
        if not isinstance(settable_values, Iterable):
            settable_values = numpy.array([settable_values])
        dimensions.append(len(settable_values))

    if loops is not None:
        dimensions.append(loops)
    return dimensions
