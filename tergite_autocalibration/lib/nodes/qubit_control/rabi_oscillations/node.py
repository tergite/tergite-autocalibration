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

from tergite_autocalibration.lib.nodes.qubit_control.rabi_oscillations.analysis import (
    NRabiNodeAnalysis,
    RabiNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.qubit_control.rabi_oscillations.measurement import (
    NRabiOscillationsMeasurement,
    RabiOscillationsMeasurement,
)
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode


class RabiOscillationsNode(ScheduleNode):
    measurement_obj = RabiOscillationsMeasurement
    analysis_obj = RabiNodeAnalysis
    qubit_qois = ["rxy:amp180"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.schedule_samplespace = {
            "mw_amplitudes": {
                qubit: np.linspace(0.002, 0.90, 61) for qubit in self.all_qubits
            }
        }


class RabiOscillations12Node(ScheduleNode):
    measurement_obj = RabiOscillationsMeasurement
    analysis_obj = RabiNodeAnalysis
    qubit_qois = ["r12:ef_amp180"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.qubit_state = 1
        self.schedule_keywords["qubit_state"] = self.qubit_state

        self.schedule_samplespace = {
            "mw_amplitudes": {
                qubit: np.linspace(0.002, 0.800, 61) for qubit in self.all_qubits
            }
        }


class NRabiOscillationsNode(ScheduleNode):
    measurement_obj = NRabiOscillationsMeasurement
    analysis_obj = NRabiNodeAnalysis
    qubit_qois = ["rxy:amp180"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.qubit_state = 0
        self.schedule_keywords["qubit_state"] = self.qubit_state

        self.schedule_samplespace = {
            "mw_amplitudes_sweep": {
                qubit: np.linspace(-0.045, 0.045, 40) for qubit in self.all_qubits
            },
            "X_repetitions": {qubit: np.arange(1, 19, 6) for qubit in self.all_qubits},
        }


class NRabiOscillations12Node(ScheduleNode):
    measurement_obj = NRabiOscillationsMeasurement
    analysis_obj = NRabiNodeAnalysis
    qubit_qois = ["r12:ef_amp180"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.qubit_state = 1
        self.schedule_keywords["qubit_state"] = self.qubit_state

        self.schedule_samplespace = {
            "mw_amplitudes_sweep": {
                qubit: np.linspace(-0.05, 0.05, 51) for qubit in self.all_qubits
            },
            "X_repetitions": {qubit: np.arange(1, 4, 1) for qubit in self.all_qubits},
        }
