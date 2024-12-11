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

import numpy as np

from tergite_autocalibration.lib.nodes.readout.ro_frequency_optimization.analysis import (
    OptimalRO01FrequencyNodeAnalysis,
    OptimalRO012FrequencyNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.readout.ro_frequency_optimization.measurement import (
    RO_frequency_optimization,
)
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode
from tergite_autocalibration.utils.user_input import resonator_samples


class RO_frequency_two_state_optimization_Node(ScheduleNode):
    measurement_obj = RO_frequency_optimization
    analysis_obj = OptimalRO01FrequencyNodeAnalysis
    qubit_qois = ["extended_clock_freqs:readout_2state_opt"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)

        self.schedule_samplespace = {
            "ro_opt_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            },
            "qubit_states": {
                qubit: np.array([0, 1], dtype=np.int8) for qubit in self.all_qubits
            },
        }


class RO_frequency_three_state_optimization_Node(ScheduleNode):
    measurement_obj = RO_frequency_optimization
    analysis_obj = OptimalRO012FrequencyNodeAnalysis
    qubit_qois = ["extended_clock_freqs:readout_3state_opt"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.all_qubits = all_qubits

        self.schedule_samplespace = {
            "ro_opt_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            },
            "qubit_states": {
                qubit: np.array([0, 1, 2], dtype=np.int8) for qubit in self.all_qubits
            },
        }
