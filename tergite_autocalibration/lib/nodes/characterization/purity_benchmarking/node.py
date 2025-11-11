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

from tergite_autocalibration.lib.base.node import QubitNode
from tergite_autocalibration.lib.nodes.characterization.purity_benchmarking.analysis import (
    PurityBenchmarkingNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.characterization.purity_benchmarking.measurement import (
    PurityBenchmarkingMeasurement,
)
from tergite_autocalibration.lib.nodes.external_parameter_node import (
    ExternalParameterNode,
)


class PurityBenchmarkingNode(QubitNode):
    measurement_obj = PurityBenchmarkingMeasurement
    analysis_obj = PurityBenchmarkingNodeAnalysis
    measurement_type = ExternalParameterNode
    qubit_qois = ["purity_fidelity"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.all_qubits = all_qubits
        self.schedule_keywords = schedule_keywords
        self.schedule_keywords = {}
        self.loops = 500
        self.schedule_keywords["loop_repetitions"] = self.loops

        RB_REPEATS = 4
        self.outer_schedule_samplespace = {
            "seeds": {
                qubit: np.arange(RB_REPEATS, dtype=np.int32)
                for qubit in self.all_qubits
            }
        }

        self.schedule_samplespace = {
            "number_of_cliffords": {
                qubit: np.array([0, 2, 4, 8, 16, 128, 256, 512])
                for qubit in self.all_qubits
            },
        }
