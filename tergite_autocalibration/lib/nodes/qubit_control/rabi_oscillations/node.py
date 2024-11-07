# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Amr Osman 2024
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np

from tergite_autocalibration.lib.base.node import BaseNode
from tergite_autocalibration.lib.nodes.qubit_control.rabi_oscillations.analysis import NRabiNodeAnalysis, \
    RabiNodeAnalysis
from tergite_autocalibration.lib.nodes.qubit_control.rabi_oscillations.measurement import N_Rabi_Oscillations, \
    Rabi_Oscillations


class Rabi_Oscillations_Node(BaseNode):
    measurement_obj = Rabi_Oscillations
    analysis_obj = RabiNodeAnalysis
    qubit_qois = ["rxy:amp180"]

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.schedule_samplespace = {
            "mw_amplitudes": {
                qubit: np.linspace(0.002, 0.90, 61) for qubit in self.all_qubits
            }
        }


class Rabi_Oscillations_12_Node(BaseNode):
    measurement_obj = Rabi_Oscillations
    analysis_obj = RabiNodeAnalysis
    qubit_qois = ["r12:ef_amp180"]

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.qubit_state = 1

        self.schedule_samplespace = {
            "mw_amplitudes": {
                qubit: np.linspace(0.002, 0.800, 61) for qubit in self.all_qubits
            }
        }


class N_Rabi_Oscillations_Node(BaseNode):
    measurement_obj = N_Rabi_Oscillations
    analysis_obj = NRabiNodeAnalysis
    qubit_qois = ["rxy:amp180"]

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.backup = False
        self.qubit_state = 0

        self.schedule_samplespace = {
            "mw_amplitudes_sweep": {
                qubit: np.linspace(-0.045, 0.045, 40) for qubit in self.all_qubits
            },
            "X_repetitions": {qubit: np.arange(1, 19, 6) for qubit in self.all_qubits},
        }


class N_Rabi_Oscillations_12_Node(BaseNode):
    measurement_obj = N_Rabi_Oscillations
    analysis_obj = NRabiNodeAnalysis
    qubit_qois = ["r12:ef_amp180"]

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.backup = False
        self.qubit_state = 1

        self.schedule_samplespace = {
            "mw_amplitudes_sweep": {
                qubit: np.linspace(-0.05, 0.05, 51) for qubit in self.all_qubits
            },
            "X_repetitions": {qubit: np.arange(1, 4, 1) for qubit in self.all_qubits},
        }
