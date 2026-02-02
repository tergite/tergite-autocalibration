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
import xarray
from quantify_core.analysis import fitting_models as fm

from tergite_autocalibration.config.legacy import dh
from tergite_autocalibration.lib.base.node import QubitNode
from tergite_autocalibration.lib.nodes.readout.ro_frequency_optimization.analysis import (
    OptimalRO01FrequencyNodeAnalysis,
    OptimalRO012FrequencyNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.readout.ro_frequency_optimization.measurement import (
    ROFrequencyOptimizationMeasurement,
)
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode
from tergite_autocalibration.lib.utils.samplespace import resonator_samples

resonator = fm.ResonatorModel()


class ROFrequencyOptimizationBase(QubitNode):
    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        super().__init__(name, all_qubits, couplers, **schedule_keywords)

    def generate_dummy_dataset(self, noise=False):
        dataset = xarray.Dataset()
        frequency_shift = 0.5e6

        for index, qubit in enumerate(self.all_qubits):
            vna_ro_freq = dh.get_legacy("VNA_resonator_frequencies")[qubit]
            qubit_states = self.schedule_samplespace["qubit_states"][qubit]
            data_array = np.array([])
            for qubit_state in qubit_states:
                ro_freq = vna_ro_freq - frequency_shift * qubit_state
                true_params = resonator.make_params(
                    fr=ro_freq,
                    Ql=15000,
                    Qe=20000,
                    A=0.01,
                    theta=0.5,
                    phi_v=0,
                    phi_0=0,
                )
                samples = resonator_samples(qubit)
                number_of_samples = len(samples)
                frequncies = np.linspace(samples[0], samples[-1], number_of_samples)
                true_s21 = resonator.eval(params=true_params, f=frequncies)
                np.random.seed(123)
                noise_scale = 0.02
                noise_s21 = noise_scale * (
                    np.random.randn(number_of_samples)
                    + 1j * np.random.randn(number_of_samples)
                )
                measured_s21 = true_s21
                if noise:
                    measured_s21 += noise_s21
                data_array = np.concatenate((data_array, measured_s21))

            dataset[index] = xarray.DataArray(data_array)
        return dataset


class ROFrequencyTwoStateOptimizationNode(ROFrequencyOptimizationBase):
    measurement_obj = ROFrequencyOptimizationMeasurement
    analysis_obj = OptimalRO01FrequencyNodeAnalysis
    measurement_type = ScheduleNode

    qubit_qois = ["extended_clock_freqs:readout_2state_opt"]

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        super().__init__(name, all_qubits, couplers, **schedule_keywords)

        self.schedule_samplespace = {
            "ro_opt_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            },
            "qubit_states": {
                qubit: np.array([0, 1], dtype=np.int8) for qubit in self.all_qubits
            },
        }


class ROFrequencyThreeStateOptimizationNode(ROFrequencyOptimizationBase):
    measurement_obj = ROFrequencyOptimizationMeasurement
    analysis_obj = OptimalRO012FrequencyNodeAnalysis
    measurement_type = ScheduleNode
    qubit_qois = ["extended_clock_freqs:readout_3state_opt"]

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        super().__init__(name, all_qubits, couplers, **schedule_keywords)
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
