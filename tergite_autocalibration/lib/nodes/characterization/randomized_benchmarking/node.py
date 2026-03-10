# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
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
from tergite_autocalibration.lib.nodes.characterization.randomized_benchmarking.analysis import (
    RandomizedBenchmarkingNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.characterization.randomized_benchmarking.measurement import (
    RandomizedBenchmarkingMeasurement,
)
from tergite_autocalibration.lib.nodes.schedule_node import OuterScheduleNode


class RandomizedBenchmarkingNode(QubitNode):
    name: str = "randomized_benchmarking"
    measurement_obj = RandomizedBenchmarkingMeasurement
    analysis_obj = RandomizedBenchmarkingNodeAnalysis
    measurement_type = OuterScheduleNode
    qubit_qois = ["fidelity", "fidelity_error", "leakage", "leakage_error"]

    def __init__(self, all_qubits: list[str], couplers: list[str], **schedule_keywords):
        super().__init__(all_qubits, couplers, **schedule_keywords)
        self.schedule_keywords = schedule_keywords
        self.schedule_keywords = {}
        self.loops = 500
        self.schedule_keywords["loop_repetitions"] = self.loops
        self.schedule_keywords["multiplexing"] = (
            "one_by_one"  # 'one_by_one' | 'parallel'
        )

        self.RB_REPEATS = 4
        self.outer_schedule_samplespace = {
            "seeds": {
                qubit: np.arange(self.RB_REPEATS, dtype=np.int32)
                for qubit in self.all_qubits
            }
        }

        self.schedule_samplespace = {
            "number_of_cliffords": {
                qubit: np.array([0, 8, 16, 32, 64, 128, 256, 512, 1024])
                for qubit in self.all_qubits
            },
            # available gates for interleaving: 'Standard' -> no interleave
            # 'X', 'Y', 'X90', 'Y90'
            "interleave_gate": {qubit: np.array(["Standard"]) for qubit in self.all_qubits},
        }

    def generate_dummy_dataset(self):
        dataset = xarray.Dataset()
        for index, qubit in enumerate(self.all_qubits):
            samples = self.schedule_samplespace["number_of_cliffords"][qubit]
            number_of_samples = len(samples) * self.loops
            noise_scale = 0.005 * index
            np.random.seed(123)
            measured_s21 = np.random.rand(number_of_samples)
            data_array = xarray.DataArray(measured_s21)
            dataset[index] = data_array
        return dataset
