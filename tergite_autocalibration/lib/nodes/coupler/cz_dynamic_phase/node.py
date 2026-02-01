# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024, 2025, 2026
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Amr Osman 2024
# (C) Copyright Chalmers Next Labs 2024, 2025, 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np

from tergite_autocalibration.lib.base.node import CouplerNode
from tergite_autocalibration.lib.nodes.coupler.cz_dynamic_phase.analysis import (
    CZ_DynamicPhaseNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_dynamic_phase.measurement import (
    CZ_DynamicPhaseMeasurement,
)
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode


class CZ_DynamicPhaseNode(CouplerNode):
    measurement_obj = CZ_DynamicPhaseMeasurement
    analysis_obj = CZ_DynamicPhaseNodeAnalysis
    measurement_type = ScheduleNode
    coupler_qois = ["control_local_phase", "target_local_phase"]

    def __init__(self, name: str, couplers: list[str], **schedule_keywords):
        super().__init__(name, couplers, **schedule_keywords)
        self.couplers = couplers

        self.coupled_qubits = self.get_coupled_qubits()
        # self.all_qubits refers to the qubits that are going to be measured
        # with the two-tones schedule
        self.all_qubits = self.coupled_qubits

        self.schedule_keywords["loop_repetitions"] = 512
        self.loops = self.schedule_keywords["loop_repetitions"]
        self.schedule_keywords["coupler_dict"] = self.gate_qubit_types_dict()

        self.schedule_samplespace = {
            "local_phases": {
                qubit: np.linspace(0, 360, 45) for qubit in self.coupled_qubits
            },
            "gate_modes": {
                coupler: np.array([True, False]) for coupler in self.couplers
            },
            "swap": {coupler: np.array([False, True]) for coupler in self.couplers},
        }
