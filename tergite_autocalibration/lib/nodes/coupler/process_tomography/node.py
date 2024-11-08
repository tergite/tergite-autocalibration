# This code is part of Tergite
#
# (C) Copyright Liangyu Chen 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np

from tergite_autocalibration.lib.base.node import BaseNode
from tergite_autocalibration.lib.nodes.coupler.process_tomography.analysis import (
    ProcessTomographyAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.process_tomography.measurement import (
    Process_Tomography,
)


class Process_Tomography_Node(BaseNode):
    measurement_obj = Process_Tomography
    analysis_obj = ProcessTomographyAnalysis

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary
    ):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = couplers[0]
        # print(couplers)
        self.coupled_qubits = couplers[0].split(sep="_")
        # print(self.coupled_qubits)
        # self.node_dictionary = kwargs
        self.redis_field = [
            "pop_g",
            "pop_e",
            "pop_f",
        ]
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.
        self.schedule_samplespace = {
            "control_ons": {coupler: range(9) for coupler in self.couplers},
            "ramsey_phases": {
                coupler: np.append(range(16), [0, 1, 2]) for coupler in self.couplers
            },
        }
        # self.validate()
