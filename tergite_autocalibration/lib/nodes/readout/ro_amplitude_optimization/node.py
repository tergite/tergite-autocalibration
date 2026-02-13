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
import xarray

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.lib.base.node import QubitNode
from tergite_autocalibration.lib.nodes.readout.ro_amplitude_optimization.analysis import (
    OptimalROThreeStateAmplitudeNodeAnalysis,
    OptimalROTwoStateAmplitudeNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.readout.ro_amplitude_optimization.measurement import (
    ROAmplitudeOptimizationMeasurement,
)
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode
from tergite_autocalibration.lib.utils.functions import isosceles_triangle


class ROAmplitudeTwoStateOptimizationNode(QubitNode):
    name: str = "ro_amplitude_two_state_optimization"
    measurement_obj = ROAmplitudeOptimizationMeasurement
    analysis_obj = OptimalROTwoStateAmplitudeNodeAnalysis
    measurement_type = ScheduleNode
    qubit_qois = [
        "measure_2state_opt:pulse_amp",
        "measure_2state_opt:acq_rotation",
        "measure_2state_opt:acq_threshold",
        "lda_coef_0",
        "lda_coef_1",
        "lda_intercept",
    ]

    def __init__(self, all_qubits: list[str], couplers: list[str], **schedule_keywords):
        super().__init__(all_qubits, couplers, **schedule_keywords)
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

    def generate_dummy_dataset(self):
        dataset = xarray.Dataset()

        first_qubit = self.all_qubits[0]
        ro_amplitudes = self.schedule_samplespace["ro_amplitudes"][first_qubit]

        def get_shot():
            data_array = np.array([])
            for ampl_index, _ in enumerate(ro_amplitudes):
                triangle_size = ampl_index + 0.05
                center_0, center_1, center_2 = isosceles_triangle(
                    base_length=3 * triangle_size, height=5 * triangle_size
                )
                iq_point_0 = np.random.normal(loc=center_0, size=(1, 2), scale=0.7)
                iq_point_1 = np.random.normal(loc=center_1, size=(1, 2), scale=0.7)
                iq_point_2 = np.random.normal(loc=center_2, size=(1, 2), scale=0.7)
                shot_0 = iq_point_0[:, 0] + 1j * iq_point_0[:, 1]
                shot_1 = iq_point_1[:, 0] + 1j * iq_point_1[:, 1]
                shot_2 = iq_point_2[:, 0] + 1j * iq_point_2[:, 1]
                shots_array = np.concatenate((shot_0, shot_1)).ravel()
                data_array = np.concatenate((shots_array, data_array))
            return data_array

        for index, _ in enumerate(self.all_qubits):

            all_shots_array = np.concatenate(
                [get_shot() for _ in range(self.loops)]
            ).ravel()

            dataset[index] = xarray.DataArray(all_shots_array)
        return dataset


class ROAmplitudeThreeStateOptimizationNode(QubitNode):
    name: str = "ro_amplitude_three_state_optimization"
    measurement_obj = ROAmplitudeOptimizationMeasurement
    analysis_obj = OptimalROThreeStateAmplitudeNodeAnalysis
    measurement_type = ScheduleNode
    qubit_qois = [
        "measure_3state_opt:pulse_amp",
        "centroid_I",
        "centroid_Q",
        "omega_01",
        "omega_12",
        "omega_20",
        "inv_cm_opt",
    ]

    def __init__(self, all_qubits: list[str], couplers: list[str], **schedule_keywords):
        super().__init__(all_qubits, couplers, **schedule_keywords)
        self.qubit_state = 2
        self.loops = 1000
        self.schedule_keywords["loop_repetitions"] = self.loops
        self.schedule_keywords["qubit_state"] = self.qubit_state

        self.schedule_samplespace = {
            "qubit_states": {
                qubit: np.array([0, 1, 2], dtype=np.int16) for qubit in self.all_qubits
            },
            "ro_amplitudes": {
                qubit: np.linspace(
                    self.punchout_amplitude(qubit) / 2.5,
                    self.punchout_amplitude(qubit) * 1.4,
                    30,
                )
                for qubit in self.all_qubits
            },
        }

    def punchout_amplitude(self, qubit: str):
        return float(REDIS_CONNECTION.hget(f"transmons:{qubit}", "measure:pulse_amp"))

    def generate_dummy_dataset(self):
        dataset = xarray.Dataset()

        first_qubit = self.all_qubits[0]
        ro_amplitudes = self.schedule_samplespace["ro_amplitudes"][first_qubit]

        def get_shot():
            data_array = np.array([])
            for ampl_index, _ in enumerate(ro_amplitudes):
                triangle_size = ampl_index + 0.05
                center_0, center_1, center_2 = isosceles_triangle(
                    base_length=3 * triangle_size, height=5 * triangle_size
                )
                iq_point_0 = np.random.normal(loc=center_0, size=(1, 2), scale=0.7)
                iq_point_1 = np.random.normal(loc=center_1, size=(1, 2), scale=0.7)
                iq_point_2 = np.random.normal(loc=center_2, size=(1, 2), scale=0.7)
                shot_0 = iq_point_0[:, 0] + 1j * iq_point_0[:, 1]
                shot_1 = iq_point_1[:, 0] + 1j * iq_point_1[:, 1]
                shot_2 = iq_point_2[:, 0] + 1j * iq_point_2[:, 1]
                shots_array = np.concatenate((shot_0, shot_1, shot_2)).ravel()
                data_array = np.concatenate((shots_array, data_array))
            return data_array

        for index, _ in enumerate(self.all_qubits):

            all_shots_array = np.concatenate(
                [get_shot() for _ in range(self.loops)]
            ).ravel()

            dataset[index] = xarray.DataArray(all_shots_array)
        return dataset


class ThreeStateDiscriminationNode(QubitNode):
    name: str = "three_state_discrimination"
    measurement_obj = ROAmplitudeOptimizationMeasurement
    analysis_obj = OptimalROThreeStateAmplitudeNodeAnalysis
    measurement_type = ScheduleNode
    qubit_qois = [
        "measure_3state_opt:pulse_amp",
        "centroid_I",
        "centroid_Q",
        "omega_01",
        "omega_12",
        "omega_20",
        "inv_cm_opt",
    ]

    def __init__(self, all_qubits: list[str], couplers: list[str], **schedule_keywords):
        super().__init__(all_qubits, couplers, **schedule_keywords)
        self.qubit_state = 2
        self.loops = 1000
        self.schedule_keywords["loop_repetitions"] = self.loops
        self.schedule_keywords["qubit_state"] = self.qubit_state

        self.schedule_samplespace = {
            "qubit_states": {
                qubit: np.array([0, 1, 2], dtype=np.int16) for qubit in self.all_qubits
            },
            "ro_amplitudes": {
                qubit: np.array([self.optimal_3state_amplitude(qubit)])
                for qubit in self.all_qubits
            },
        }

    def optimal_3state_amplitude(self, qubit: str):
        return float(
            REDIS_CONNECTION.hget(f"transmons:{qubit}", "measure_3state_opt:pulse_amp")
        )

    def generate_dummy_dataset(self):
        dataset = xarray.Dataset()

        first_qubit = self.all_qubits[0]
        ro_amplitudes = self.schedule_samplespace["ro_amplitudes"][first_qubit]

        def get_shot():
            data_array = np.array([])
            for ampl_index, _ in enumerate(ro_amplitudes):
                triangle_size = ampl_index + 0.05
                center_0, center_1, center_2 = isosceles_triangle(
                    base_length=3 * triangle_size, height=5 * triangle_size
                )
                iq_point_0 = np.random.normal(loc=center_0, size=(1, 2), scale=0.7)
                iq_point_1 = np.random.normal(loc=center_1, size=(1, 2), scale=0.7)
                iq_point_2 = np.random.normal(loc=center_2, size=(1, 2), scale=0.7)
                shot_0 = iq_point_0[:, 0] + 1j * iq_point_0[:, 1]
                shot_1 = iq_point_1[:, 0] + 1j * iq_point_1[:, 1]
                shot_2 = iq_point_2[:, 0] + 1j * iq_point_2[:, 1]
                shots_array = np.concatenate((shot_0, shot_1, shot_2)).ravel()
                data_array = np.concatenate((shots_array, data_array))
            return data_array

        for index, _ in enumerate(self.all_qubits):

            all_shots_array = np.concatenate(
                [get_shot() for _ in range(self.loops)]
            ).ravel()

            dataset[index] = xarray.DataArray(all_shots_array)
        return dataset
