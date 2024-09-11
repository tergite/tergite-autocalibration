# This code is part of Tergite
#
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

from .analysis import All_XY_Analysis
from .measurement import All_XY
from ....base.node import BaseNode


class All_XY_Node(BaseNode):
    measurement_obj = All_XY
    analysis_obj = All_XY_Analysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.all_qubits = all_qubits
        self.redis_field = ["error_syndromes"]
        self.backup = False
        # TODO properly set the dimensions
        self.schedule_samplespace = {
            "XY_index": {qubit: np.array(range(23)) for qubit in self.all_qubits}
        }
