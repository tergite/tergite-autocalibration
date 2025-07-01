# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
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

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.lib.nodes.readout.ro_amplitude_optimization.analysis import (
    OptimalROThreeStateAmplitudeNodeAnalysis,
    OptimalROTwoStateAmplitudeNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.readout.ro_amplitude_optimization.measurement import (
    ROAmplitudeOptimizationMeasurement,
)
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleQubitNode


class ROAmplitudeTwoStateOptimizationNode(ScheduleQubitNode):
    measurement_obj = ROAmplitudeOptimizationMeasurement
    analysis_obj = OptimalROTwoStateAmplitudeNodeAnalysis
    qubit_qois = [
        "measure_2state_opt:pulse_amp",
        "measure_2state_opt:acq_rotation",
        "measure_2state_opt:acq_threshold",
    ]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.qubit_state = 1
        self.loops = 1000
        self.schedule_keywords["loop_repetitions"] = self.loops
        self.schedule_keywords["qubit_state"] = self.qubit_state
        self.plots_per_qubit = 3  #  fidelity plot, IQ shots, confusion matrix

        self.schedule_samplespace = {
            "qubit_states": {
                qubit: np.array([0, 1], dtype=np.int16) for qubit in self.all_qubits
            },
            "ro_amplitudes": {
                qubit: np.linspace(
                    self.punchout_amplitude(qubit) / 4,
                    self.punchout_amplitude(qubit) * 1.2,
                    45,
                )
                for qubit in self.all_qubits
            },
        }

    def punchout_amplitude(self, qubit: str):
        return float(REDIS_CONNECTION.hget(f"transmons:{qubit}", "measure:pulse_amp"))


class ROAmplitudeThreeStateOptimizationNode(ScheduleQubitNode):
    measurement_obj = ROAmplitudeOptimizationMeasurement
    analysis_obj = OptimalROThreeStateAmplitudeNodeAnalysis
    qubit_qois = [
        "measure_3state_opt:pulse_amp",
        "centroid_I",
        "centroid_Q",
        "omega_01",
        "omega_12",
        "omega_20",
        "inv_cm_opt",
    ]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.qubit_state = 2
        self.loops = 1000
        self.schedule_keywords["loop_repetitions"] = self.loops
        self.schedule_keywords["qubit_state"] = self.qubit_state

        self.schedule_samplespace = {
            "qubit_states": {
                qubit: np.array([0, 1, 2], dtype=np.int16) for qubit in self.all_qubits
            },
            "ro_amplitudes": {
                qubit: np.append(
                    np.linspace(0.005, 0.025, 10), np.linspace(0.026, 0.06, 7)
                )
                for qubit in self.all_qubits
            },
        }
