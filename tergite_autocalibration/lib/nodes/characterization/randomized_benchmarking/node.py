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

from tergite_autocalibration.lib.nodes.characterization.randomized_benchmarking.analysis import (
    RandomizedBenchmarkingSSRONodeAnalysis,
)
from tergite_autocalibration.lib.nodes.characterization.randomized_benchmarking.measurement import (
    RandomizedBenchmarkingSSROMeasurement,
)
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode


class RandomizedBenchmarkingSSRONode(ScheduleNode):
    measurement_obj = RandomizedBenchmarkingSSROMeasurement
    analysis_obj = RandomizedBenchmarkingSSRONodeAnalysis
    qubit_qois = ["fidelity", "fidelity_error", "leakage", "leakage_error"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.schedule_keywords = schedule_keywords
        self.schedule_keywords = {}
        self.loops = 500
        self.schedule_keywords["loop_repetitions"] = self.loops

        RB_REPEATS = 2
        self.outer_schedule_samplespace = {
            "seeds": {
                qubit: np.arange(RB_REPEATS, dtype=np.int32)
                for qubit in self.all_qubits
            }
        }

        self.schedule_samplespace = {
            "number_of_cliffords": {
                qubit: np.array([0, 8, 16, 32, 64, 128, 256, 512, 1024])
                for qubit in self.all_qubits
            },
        }
