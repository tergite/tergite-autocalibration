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

from tergite_autocalibration.lib.base.node import BaseNode
from tergite_autocalibration.lib.nodes.characterization.all_xy.analysis import (
    AllXYAnalysis,
)
from tergite_autocalibration.lib.nodes.characterization.all_xy.measurement import AllXYMeasurement


class AllXYNode(BaseNode):
    measurement_obj = AllXYMeasurement
    analysis_obj = AllXYAnalysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.all_qubits = all_qubits
        self.redis_field = ["error_syndromes"]
        self.backup = False
        # TODO properly set the dimensions
        self.schedule_samplespace = {
            "XY_index": {qubit: np.array(range(23)) for qubit in self.all_qubits}
        }
