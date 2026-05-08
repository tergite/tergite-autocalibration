# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2026
# (C) Chalmers Next Labs 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from typing import Literal

import numpy as np
import xarray as xr

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.lib.base.node import CouplerNode
from tergite_autocalibration.lib.nodes.schedule_node import OuterScheduleNode


class CZ_StaticZZNode(CouplerNode):
    name: str = "cz_static_ZZ"
    measurement_obj = CZStaticZZMeasurement
    analysis_obj = CZStaticZZAnalysis
    measurement_type = OuterScheduleNode
    coupler_qois = ["cz_static_ZZ"]

    def __init__(self, couplers: list[str], **schedule_keywords):
        super().__init__(couplers, **schedule_keywords)

        self.couplers = couplers

        self.coupled_qubits = self.get_coupled_qubits()
        self.all_qubits = self.coupled_qubits
        self.validate()

        self.schedule_keywords["loop_repetitions"] = 512 // 4
        self.loops = self.schedule_keywords["loop_repetitions"]
        phase_paths = self.all_phase_paths()
        self.analysis_keywords = {
            coupler: {"phase_path": phase_paths[coupler]} for coupler in self.couplers
        }

        self.schedule_samplespace = {
            "ramsey_delays": {
                qubit: np.arange(4e-9, 2048e-9, 12 * 8e-9) for qubit in self.all_qubits
            },
            "artificial_detunings": {
                qubit: np.arange(-2.1, 2.1, 0.8) * 1e6 for qubit in self.all_qubits
            },
            "spectator_states": {
                coupler: np.arange([0, 1], dtype=np.int8) for coupler in self.couplers
            },
        }

    def all_phase_paths(self) -> dict[str, Literal["via_02", "via_20"]]:
        phase_paths = {}
        for coupler in self.couplers:
            path = REDIS_CONNECTION.hget(f"couplers:{coupler}", "cz_phase_path")
            phase_paths[coupler] = path
        return phase_paths

    def initial_operation(self):
        self.spi_manager.set_initial_parking_currents(self.couplers)

    def generate_dummy_dataset(self):
        pass
