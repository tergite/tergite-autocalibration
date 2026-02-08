# This code is part of Tergite
#
# (C) Copyright Amr Osman 2024
# (C) Copyright Eleftherios Moschandreou 2025, 2026
# (C) Copyright Pontus Vikstål 2025
# (C) Copyright Chalmers Next Labs 2025, 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.lib.base.node import CouplerNode
from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.analysis import (
    TwoQubitRBNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.measurement import (
    TwoQubitRBMeasurement,
)
from tergite_autocalibration.lib.nodes.schedule_node import OuterScheduleNode

RB_REPEATS = 7


class CZ_RB_Node(CouplerNode):
    name = "cz_rb"
    measurement_obj = TwoQubitRBMeasurement
    analysis_obj = TwoQubitRBNodeAnalysis
    measurement_type = OuterScheduleNode
    coupler_qois = ["cz_fidelity"]

    def __init__(self, couplers: list[str], **schedule_keywords):
        super().__init__(couplers, **schedule_keywords)
        self.couplers = couplers
        self.loops = 500
        self.schedule_keywords["loop_repetitions"] = self.loops
        self.coupled_qubits = self.get_coupled_qubits()
        self.all_qubits = self.coupled_qubits
        #    self.schedule_keywords["interleaving_clifford_id"] = 4386
        self.schedule_keywords["coupler_dict"] = self.gate_qubit_types_dict()

        self.outer_schedule_samplespace = {
            "seeds": {
                # coupler: np.array([23, 27, 49], dtype=np.int32)
                coupler: np.arange(RB_REPEATS, dtype=np.int32)
                for coupler in self.couplers
            }
        }

        self.schedule_samplespace = {
            "number_of_cliffords": {
                # coupler: np.array([1])
                # coupler: np.array([1, 2, 3, 4])
                # coupler: np.array([0, 1, 2, 3, 4, 8, 10, 16, 22, 32, 64, 128, 256])
                coupler: np.array([0, 1, 2, 3, 4, 8, 16, 32, 64])
                for coupler in self.couplers
            },
            "interleave_modes": {
                coupler: np.array([False, True]) for coupler in self.couplers
            },
            # "cz_pulse_frequencies": {
            #     coupler: np.linspace(-0.5e6, 0.5e6, 5) + self.cz_frequency(coupler)
            #     for coupler in self.couplers
            # },
        }

    def cz_frequency(self, coupler):
        cz_freq = float(
            REDIS_CONNECTION.hget(f"coupler:{coupler}", "cz_pulse_frequency")
        )
        return cz_freq

    def initial_operation(self):
        self.spi_manager.set_parking_currents(self.couplers)
