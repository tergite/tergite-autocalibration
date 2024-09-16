# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np

from .analysis import (
    OptimalRO_Two_state_AmplitudeAnalysis,
    OptimalRO_Three_state_AmplitudeAnalysis,
)
from .measurement import RO_amplitude_optimization
from ....base.node import BaseNode


class RO_amplitude_two_state_optimization_Node(BaseNode):
    measurement_obj = RO_amplitude_optimization
    analysis_obj = OptimalRO_Two_state_AmplitudeAnalysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.all_qubits = all_qubits
        self.redis_field = [
            "measure_2state_opt:ro_ampl_2st_opt",
            "measure_2state_opt:rotation",
            "measure_2state_opt:threshold",
        ]
        self.qubit_state = 1
        # FIXME: This is a sort of hack to ignore the couplers
        self.schedule_keywords = {}
        self.schedule_keywords["loop_repetitions"] = 1000
        self.plots_per_qubit = 3  #  fidelity plot, IQ shots, confusion matrix

        self.loops = self.schedule_keywords["loop_repetitions"]

        self.schedule_samplespace = {
            "qubit_states": {
                qubit: np.tile(np.array([0, 1], dtype=np.int16), self.loops)
                for qubit in self.all_qubits
            },
            "ro_amplitudes": {
                qubit: np.linspace(0.001, 0.01, 11) for qubit in self.all_qubits
            },
        }


class RO_amplitude_three_state_optimization_Node(BaseNode):
    measurement_obj = RO_amplitude_optimization
    analysis_obj = OptimalRO_Three_state_AmplitudeAnalysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.all_qubits = all_qubits
        self.redis_field = ["measure_3state_opt:ro_ampl_3st_opt", "inv_cm_opt"]
        self.qubit_state = 2
        self.schedule_keywords = {}
        self.schedule_keywords["loop_repetitions"] = 1000
        self.plots_per_qubit = 3  #  fidelity plot, IQ shots, confusion matrix
        self.loops = self.schedule_keywords["loop_repetitions"]

        self.schedule_samplespace = {
            "qubit_states": {
                qubit: np.tile(np.array([0, 1, 2], dtype=np.int16), self.loops)
                for qubit in self.all_qubits
            },
            # FIXME: Check on whether the samplespace can be bigger
            "ro_amplitudes": {
                qubit: np.append(
                    np.linspace(0.001, 0.025, 5), np.linspace(0.026, 0.2, 5)
                )
                for qubit in self.all_qubits
            },
        }