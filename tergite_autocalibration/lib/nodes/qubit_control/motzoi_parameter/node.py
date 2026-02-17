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
import xarray

from tergite_autocalibration.lib.base.node import QubitNode
from tergite_autocalibration.lib.nodes.qubit_control.motzoi_parameter.analysis import (
    Motzoi01NodeAnalysis,
    Motzoi12NodeAnalysis,
)
from tergite_autocalibration.lib.nodes.qubit_control.motzoi_parameter.measurement import (
    MotzoiParameterMeasurement,
)
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode
from tergite_autocalibration.lib.utils.analysis_models import RabiModel

rabi = RabiModel()


class MotzoiParameterNode(QubitNode):
    name: str = "motzoi_parameter"
    measurement_obj = MotzoiParameterMeasurement
    analysis_obj = Motzoi01NodeAnalysis
    measurement_type = ScheduleNode
    qubit_qois = ["rxy:motzoi"]

    def __init__(self, all_qubits: list[str], couplers: list[str], **schedule_keywords):
        super().__init__(all_qubits, couplers, **schedule_keywords)
        self.motzoi_minima = []  # NOTE: is this needed?
        self.qubit_state = 0
        self.schedule_keywords["qubit_state"] = self.qubit_state
        self.schedule_samplespace = {
            "mw_motzois": {
                qubit: np.linspace(-0.4, 0.1, 40) for qubit in self.all_qubits
            },
            "X_repetitions": {qubit: np.arange(1, 19, 6) for qubit in self.all_qubits},
        }

    def generate_dummy_dataset(self):
        dataset = xarray.Dataset()
        real_motzoi = -0.1
        first_qubit = self.all_qubits[0]
        x_repetitions = self.schedule_samplespace["X_repetitions"][first_qubit]
        for index, _ in enumerate(self.all_qubits):
            data_array = np.array([])
            for number_of_Xs in x_repetitions:
                this_frequency = number_of_Xs / 2
                # find the phase that produces minimum at the real_motzoi
                this_phase = np.pi - 2 * np.pi * this_frequency * real_motzoi
                true_params = rabi.make_params(
                    amplitude=0.2,
                    frequency=this_frequency,
                    offset=0.2,
                    phase=this_phase,
                )
                samples = self.schedule_samplespace["mw_motzois"][first_qubit]
                number_of_samples = len(samples)
                fit_samples = np.linspace(samples[0], samples[-1], number_of_samples)
                true_s21 = rabi.eval(params=true_params, drive_amp=fit_samples)
                noise_scale = 0.02

                np.random.seed(123)
                measured_s21 = true_s21 + 0 * noise_scale * (
                    np.random.randn(number_of_samples)
                    + 1j * np.random.randn(number_of_samples)
                )
                data_array = np.concatenate((data_array, measured_s21))

            # Add the DataArray to the Dataset with an integer name (converted to string)
            dataset[index] = xarray.DataArray(data_array)
        return dataset


class MotzoiParameter12Node(QubitNode):
    name: str = "motzoi_parameter_12"
    measurement_obj = MotzoiParameterMeasurement
    analysis_obj = Motzoi12NodeAnalysis
    measurement_type = ScheduleNode
    qubit_qois = ["r12:ef_motzoi"]

    def __init__(self, all_qubits: list[str], couplers: list[str], **schedule_keywords):
        super().__init__(all_qubits, couplers, **schedule_keywords)
        self.motzoi_minima = []  # NOTE: is this needed?
        self.qubit_state = 1
        self.schedule_keywords["qubit_state"] = self.qubit_state
        self.schedule_samplespace = {
            "mw_motzois": {
                qubit: np.linspace(-0.3, 0.3, 51) for qubit in self.all_qubits
            },
            "X_repetitions": {qubit: np.arange(1, 4, 1) for qubit in self.all_qubits},
        }
