# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Amr Osman 2024
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np

from tergite_autocalibration.lib.nodes.qubit_control.ramsey_fringes.analysis import (
    RamseyDetunings01NodeAnalysis,
    RamseyDetunings12NodeAnalysis,
)
from tergite_autocalibration.lib.nodes.qubit_control.ramsey_fringes.measurement import (
    RamseyDetuningsMeasurement,
)
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleQubitNode


class RamseyFringes12Node(ScheduleQubitNode):
    measurement_obj = RamseyDetuningsMeasurement
    analysis_obj = RamseyDetunings12NodeAnalysis
    qubit_qois = ["clock_freqs:f12"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.qubit_state = 1
        self.schedule_keywords["qubit_state"] = self.qubit_state
        self.schedule_samplespace = {
            "ramsey_delays": {
                qubit: np.arange(4e-9, 2048e-9, 8 * 8e-9) for qubit in self.all_qubits
            },
            "artificial_detunings": {
                qubit: np.arange(-2.1, 2.1, 0.8) * 1e6 for qubit in self.all_qubits
            },
        }


class RamseyFringesNode(ScheduleQubitNode):
    measurement_obj = RamseyDetuningsMeasurement
    analysis_obj = RamseyDetunings01NodeAnalysis
    qubit_qois = ["clock_freqs:f01"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.schedule_samplespace = {
            "ramsey_delays": {
                qubit: np.arange(4e-9, 2048e-9, 8 * 8e-9) for qubit in self.all_qubits
            },
            "artificial_detunings": {
                qubit: np.arange(-2.1, 2.1, 0.8) * 1e6 for qubit in self.all_qubits
            },
        }
