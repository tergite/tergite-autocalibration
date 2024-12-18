# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2024
# (C) Copyright Eleftherios Moschandreou 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np

from tergite_autocalibration.lib.nodes.readout.resonator_relaxation.analysis import (
    ResonatorRelaxationNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.readout.resonator_relaxation.measurement import (
    ResonatorRelaxation,
)
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode
from tergite_autocalibration.lib.utils.samplespace import resonator_samples


class ResonatorRelaxationNode(ScheduleNode):
    measurement_obj = ResonatorRelaxation
    analysis_obj = ResonatorRelaxationNodeAnalysis
    qubit_qois = ["minimum_resonator_relaxation"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)

        self.schedule_samplespace = {
            "ro_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            },
            "reset_durations": {
                qubit: np.arange(2e-6, 10e-6, 1e-6) for qubit in self.all_qubits
            },
        }
