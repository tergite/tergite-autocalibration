# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np

from tergite_autocalibration.lib.nodes.readout.punchout.analysis import (
    PunchoutNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.readout.punchout.measurement import Punchout
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode
from tergite_autocalibration.lib.utils.samplespace import resonator_samples


class Punchout_Node(ScheduleNode):
    measurement_obj = Punchout
    analysis_obj = PunchoutNodeAnalysis
    qubit_qois = ["measure:pulse_amp"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)

        self.schedule_samplespace = {
            "ro_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            },
            "ro_amplitudes": {
                qubit: np.linspace(0.008, 0.06, 2) for qubit in self.all_qubits
            },
        }
