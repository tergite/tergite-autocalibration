# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024, 2025
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
import xarray

from tergite_autocalibration.lib.base.node import QubitNode
from tergite_autocalibration.lib.nodes.qubit_control.ramsey_fringes.analysis import (
    RamseyDetunings01NodeAnalysis,
    RamseyDetunings12NodeAnalysis,
)
from tergite_autocalibration.lib.nodes.qubit_control.ramsey_fringes.measurement import (
    RamseyDetuningsMeasurement,
)

from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode
from tergite_autocalibration.lib.utils.analysis_models import RamseyModel

ramsey_model = RamseyModel()


class RamseyFringesBase(QubitNode):
    measurement_obj = RamseyDetuningsMeasurement
    analysis_obj = RamseyDetunings12NodeAnalysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)

    def generate_dummy_dataset(self, noise=False):
        dataset = xarray.Dataset()
        real_detuning = 200e3
        first_qubit = self.all_qubits[0]
        detunings = self.schedule_samplespace["artificial_detunings"][first_qubit]
        for index, _ in enumerate(self.all_qubits):
            data_array = np.array([])
            for detuning in detunings:
                measured_detuning = np.abs(detuning - real_detuning)
                true_params = ramsey_model.make_params(
                    amplitude=0.2,
                    frequency=measured_detuning,
                    tau=80e-6,
                    phase=0,
                    offset=0,
                )
                np.random.seed(123)
                noise_scale = 0.02
                samples = self.schedule_samplespace["ramsey_delays"][first_qubit]
                number_of_samples = len(samples)
                delays = np.linspace(samples[0], samples[-1], number_of_samples)
                true_s21 = ramsey_model.eval(params=true_params, t=delays)

                noise_s21 = noise_scale * (
                    np.random.randn(number_of_samples)
                    + 1j * np.random.randn(number_of_samples)
                )
                measured_s21 = true_s21
                if noise:
                    measured_s21 += noise_s21
                data_array = np.concatenate((data_array, measured_s21))

            # Add the DataArray to the Dataset with an integer name (converted to string)
            dataset[index] = xarray.DataArray(data_array)
        return dataset


class RamseyFringes12Node(RamseyFringesBase):
    qubit_qois = ["clock_freqs:f12"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.qubit_state = 1
        self.schedule_keywords["qubit_state"] = self.qubit_state
        self.schedule_samplespace = {
            "ramsey_delays": {
                qubit: np.arange(4e-9, 2048e-9, 8 * 8e-9) for qubit in self.all_qubits
            },
            "artificial_detunings": {
                qubit: np.arange(-2.1, 2.1, 0.8) * 1e6 for qubit in self.all_qubits
            },
        }


class RamseyFringesNode(RamseyFringesBase):
    measurement_obj = RamseyDetuningsMeasurement
    analysis_obj = RamseyDetunings01NodeAnalysis
    measurement_type = ScheduleNode
    qubit_qois = ["clock_freqs:f01"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.schedule_samplespace = {
            "ramsey_delays": {
                qubit: np.arange(4e-9, 2048e-9, 8 * 8e-9) for qubit in self.all_qubits
            },
            "artificial_detunings": {
                qubit: np.arange(-2.1, 2.1, 0.8) * 1e6 for qubit in self.all_qubits
            },
        }
