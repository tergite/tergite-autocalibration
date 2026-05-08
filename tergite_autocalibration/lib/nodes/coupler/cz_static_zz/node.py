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

import numpy as np
import xarray as xr

from tergite_autocalibration.lib.base.node import CouplerNode
from tergite_autocalibration.lib.nodes.coupler.cz_static_zz.analysis import (
    ZZCouplingNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_static_zz.measurement import (
    ZZCouplingMeasurement,
)
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode


class ZZCouplingNode(CouplerNode):
    name: str = "zz_coupling"
    measurement_obj = ZZCouplingMeasurement
    analysis_obj = ZZCouplingNodeAnalysis
    measurement_type = ScheduleNode
    coupler_qois = ["zz_coupling"]

    def __init__(self, couplers: list[str], **schedule_keywords):
        super().__init__(couplers, **schedule_keywords)

        self.couplers = couplers

        self.coupled_qubits = self.get_coupled_qubits()
        self.all_qubits = self.coupled_qubits
        self.validate()

        self.schedule_keywords["coupler_dict"] = self.qubit_types()

        self.schedule_samplespace = {
            "ramsey_delays": {
                qubit: np.arange(4e-9, 2048e-9, 12 * 8e-9) for qubit in self.all_qubits
            },
            "artificial_detunings": {
                qubit: np.arange(-2.1, 2.1, 0.8) * 1e6 for qubit in self.all_qubits
            },
            "spectator_states": {
                coupler: np.array([0, 1], dtype=np.int8) for coupler in self.couplers
            },
        }

    def qubit_types(self) -> dict[str, dict]:
        qubit_types_dict = {}
        for coupler in self.couplers:
            # NOTE: as is the, the convention is that the first qubit is active
            # and the second is spectator
            active_qubit, spectator_qubit = coupler.split("_")
            qubit_types_dict[coupler] = {
                "active_qubit": active_qubit,
                "spectator_qubit": spectator_qubit,
            }
        return qubit_types_dict

    def initial_operation(self):
        self.spi_manager.set_initial_parking_currents(self.couplers)

    def generate_dummy_dataset(self):
        pass
