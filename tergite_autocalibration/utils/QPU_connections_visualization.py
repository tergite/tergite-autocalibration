# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023
# (C) Copyright Liangyu Chen 2023
# (c) Copyright Stefan Hill 2023
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from dataclasses import dataclass

import numpy as np

from tergite_autocalibration.config.VNA_values import (
    VNA_qubit_frequencies,
    VNA_resonator_frequencies,
    VNA_f12_frequencies,
)


@dataclass
class QPU_element:
    label: str
    XY_line: str
    module: int
    grid_coords: tuple[int, int]

    def __post_init__(self):
        self.res_freq = VNA_resonator_frequencies[self.label]
        self.qubit_freq = VNA_qubit_frequencies[self.label]
        self.qubit_f12 = VNA_f12_frequencies[self.label]
        self.LO: float
        self.IF: float
        self.IF_12: float


QPU = [
    #        QPU_element('q11', 'D6', 1, (0,2)),
    #        QPU_element('q12', 'A1', 2, (1,2)),
    #        QPU_element('q13', 'A5', 3, (2,2)),
    #        QPU_element('q14', 'A9', 4, (3,2)),
    #        QPU_element('q15', 'D4', 5, (4,2)),
    QPU_element("q16", "A3", 6, (0, 1)),
    QPU_element("q17", "D2", 7, (1, 1)),
    QPU_element("q18", "A2", 8, (2, 1)),
    QPU_element("q19", "D3", 9, (3, 1)),
    QPU_element("q20", "A8", 10, (4, 1)),
    QPU_element("q21", "D5", 11, (0, 0)),
    QPU_element("q22", "A4", 12, (1, 0)),
    QPU_element("q23", "A6", 13, (2, 0)),
    QPU_element("q24", "D7", 14, (3, 0)),
    QPU_element("q25", "A7", 15, (4, 0)),
]

def distance(element_1, element_2) -> int:
    x_distance = np.abs(element_1.grid_coords[0] - element_2.grid_coords[0])
    y_distance = np.abs(element_1.grid_coords[1] - element_2.grid_coords[1])
    return x_distance + y_distance


LO_group = 3.511e9
LO_16 = 3.295e9
LO_17 = 4.055e9
LO_20 = 3.455e9
LO_25 = 4.124e9
LO_21 = 3.884e9
LO_22 = 3.445e9
collision_tol = 6.5e6


def hits_neighbors(qubit: str, lo_freq: float):
    for q in QPU:
        if q.label == qubit:
            element = q

    neighbour_qubits = list(
        filter(lambda element_: distance(element, element_) == 1, QPU)
    )

    # print(f'{ neighbour_qubits = }')
    f01 = VNA_qubit_frequencies[qubit]
    f12 = VNA_f12_frequencies[qubit]
    i_freq = f01 - lo_freq
    i_freq_12 = f12 - lo_freq

    element.LO = lo_freq
    element.IF = i_freq
    element.IF_12 = i_freq_12

    mirror = lo_freq - i_freq
    harmonics = {
        "mirror": mirror,
        "h_harm_2": lo_freq - 2 * i_freq,
        "h_harm_3": lo_freq - 3 * i_freq,
        "l_harm_2": lo_freq + 2 * i_freq,
        "l_harm_3": lo_freq + 3 * i_freq,
    }

    for harmonic, harmonic_freq in harmonics.items():
        if np.abs(harmonic_freq - f12) < collision_tol:
            print(
                f"{qubit} harmonic {harmonic} hits f12 at distance {np.abs(harmonic_freq-f12)/1e6}MHz"
            )

    for neighbour_element in neighbour_qubits:
        neighbour_qubit = neighbour_element.label
        neighbour_f01 = VNA_qubit_frequencies[neighbour_qubit]
        neighbour_f12 = VNA_f12_frequencies[neighbour_qubit]
        for harmonic, harmonic_freq in harmonics.items():
            if np.abs(harmonic_freq - neighbour_f01) < collision_tol:
                print(
                    f"{qubit} harmonic {harmonic} hits neighbour_f01: {neighbour_f01} of {neighbour_qubit} at distance {(neighbour_f01-harmonic_freq)/1e6}MHz"
                )
            if np.abs(harmonic_freq - neighbour_f12) < collision_tol:
                print(
                    f"{qubit} harmonic {harmonic} hits neighbour_f12: {neighbour_f12} of {neighbour_qubit} at distance {(neighbour_f12-harmonic_freq)/1e6}MHz"
                )


# group_qubits = ['q11', 'q12', 'q13', 'q14', 'q15', 'q16', 'q17','q18', 'q19', 'q20', 'q23', 'q24', 'q25']
group_qubits = ["q18", "q19", "q20", "q23", "q24", "q25"]
[hits_neighbors(q, LO_group) for q in group_qubits]

hits_neighbors("q16", LO_16)
hits_neighbors("q17", LO_17)
hits_neighbors("q21", LO_21)
hits_neighbors("q22", LO_22)
hits_neighbors("q20", LO_20)
hits_neighbors("q25", LO_25)

