# This code is part of Tergite
#
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Amr Osman 2024
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
from tergite_autocalibration.lib.nodes.coupler.reset_chevron.analysis import (
    ResetChevronNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.reset_chevron.measurement import (
    ResetChevronDCMeasurement,
)


class ResetChevronNode(BaseNode):
    measurement_obj = ResetChevronDCMeasurement
    analysis_obj = ResetChevronNodeAnalysis
    coupler_qois = ["reset_amplitude_qc", "reset_duration_qc"]

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.qubit_state = 0
        self.all_qubits = [q for bus in couplers for q in bus.split("_")]
        self.coupler_samplespace = self.samplespace

        self.schedule_samplespace = {
            "reset_pulse_durations": {
                coupler: 1e-9 + np.linspace(0, 240, 41) * 1e-9
                for coupler in self.couplers
            },
            "reset_pulse_amplitudes": {
                coupler: np.linspace(-0.12, -0.26, 21) for coupler in self.couplers
            },
        }

        self.validate()

    def validate(self) -> None:
        all_coupled_qubits = []
        for coupler in self.couplers:
            all_coupled_qubits += coupler.split("_")
        if len(all_coupled_qubits) > len(set(all_coupled_qubits)):
            print("Couplers share qubits")
            raise ValueError("Improper Couplers")
