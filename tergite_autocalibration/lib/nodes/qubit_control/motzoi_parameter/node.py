# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
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

from tergite_autocalibration.lib.nodes.qubit_control.motzoi_parameter.analysis import (
    Motzoi01NodeAnalysis,
    Motzoi12NodeAnalysis,
)
from tergite_autocalibration.lib.nodes.qubit_control.motzoi_parameter.measurement import (
    Motzoi_parameter,
)
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode


class Motzoi_Parameter_Node(ScheduleNode):
    measurement_obj = Motzoi_parameter
    analysis_obj = Motzoi01NodeAnalysis
    qubit_qois = ["rxy:motzoi"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.motzoi_minima = []  # NOTE: is this needed?
        self.qubit_state = 0
        self.schedule_keywords["qubit_state"] = self.qubit_state
        self.schedule_samplespace = {
            "mw_motzois": {
                qubit: np.linspace(-0.4, 0.1, 51) for qubit in self.all_qubits
            },
            "X_repetitions": {qubit: np.arange(1, 19, 6) for qubit in self.all_qubits},
        }


class Motzoi_Parameter_12_Node(ScheduleNode):
    measurement_obj = Motzoi_parameter
    analysis_obj = Motzoi12NodeAnalysis
    qubit_qois = ["r12:ef_motzoi"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.motzoi_minima = []  # NOTE: is this needed?
        self.qubit_state = 1
        self.schedule_keywords["qubit_state"] = self.qubit_state
        self.schedule_samplespace = {
            "mw_motzois": {
                qubit: np.linspace(-0.3, 0.3, 51) for qubit in self.all_qubits
            },
            "X_repetitions": {qubit: np.arange(1, 4, 1) for qubit in self.all_qubits},
        }
