# This code is part of Tergite
#
# (C) Copyright Joel Sandås 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np

from tergite_autocalibration.lib.base.schedule_node import ScheduleNode
from tergite_autocalibration.lib.nodes.characterization.purity_benchmarking.analysis import (
    PurityBenchmarkingNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.characterization.purity_benchmarking.measurement import (
    PurityBenchmarkingMeasurement,
)
<<<<<<< HEAD
=======
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode
>>>>>>> eleftherios/fix/fix-ro-amplitude-optimizations


class PurityBenchmarkingNode(ScheduleNode):
    measurement_obj = PurityBenchmarkingMeasurement
    analysis_obj = PurityBenchmarkingNodeAnalysis
    qubit_qois = ["purity_fidelity"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.schedule_keywords = schedule_keywords
        self.schedule_keywords = {}

        self.schedule_samplespace = {
            "number_of_cliffords": {
                # qubit: all_numbers for qubit in self.all_qubits
                # qubit: np.array([2, 16, 128, 256,512, 768, 1024, 0, 1]) for qubit in self.all_qubits
                qubit: self.stack_number_of_cliffords([0, 2, 4, 8, 16, 128, 256, 512])
                for qubit in self.all_qubits
            },
        }

        RB_REPEATS = 2
        self.outer_schedule_samplespace = {
            "seeds": {
                qubit: np.arange(RB_REPEATS, dtype=np.int32)
                for qubit in self.all_qubits
            }
        }

    def stack_number_of_cliffords(self, number_of_cliffords):
        return np.array(list(number_of_cliffords) * 3 + [0, 1, 2])
