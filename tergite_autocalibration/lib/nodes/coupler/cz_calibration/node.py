# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
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

from .analysis import (
    CZCalibrationSSRONodeAnalysis,
    ResetCalibrationSSRONodeAnalysis,
)
from .measurement import (
    CZ_calibration,
    CZ_calibration_SSRO,
    Reset_calibration_SSRO,
)
from ....base.node import BaseNode


class CZCalibrationSSRONode(BaseNode):
    measurement_obj = CZ_calibration_SSRO
    analysis_obj = CZCalibrationSSRONodeAnalysis

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.coupler = couplers[0]
        self.coupled_qubits = couplers[0].split(sep="_")
        self.edges = couplers
        self.redis_field = ["cz_phase", "cz_pop_loss", "cz_leakage"]
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.
        self.schedule_keywords = schedule_keywords
        self.schedule_keywords["dynamic"] = False
        self.schedule_keywords["swap_type"] = False

        self.schedule_samplespace = {
            "control_ons": {coupler: [False, True] for coupler in self.couplers},
            "ramsey_phases": {
                coupler: np.append(np.linspace(0, 720, 25), [0, 1, 2])
                for coupler in self.couplers
            },
        }


class CZCalibrationSwapSSRONode(BaseNode):
    measurement_obj = CZ_calibration_SSRO
    analysis_obj = CZCalibrationSSRONodeAnalysis

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.coupler = couplers[0]
        self.coupled_qubits = couplers[0].split(sep="_")
        self.edges = couplers
        self.redis_field = ["cz_phase", "cz_pop_loss", "cz_leakage"]
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.
        self.schedule_keywords["dynamic"] = False
        self.schedule_keywords["swap_type"] = True
        self.schedule_samplespace = {
            "control_ons": {qubit: [False, True] for qubit in self.coupled_qubits},
            "ramsey_phases": {
                qubit: np.linspace(0, 360, 25) for qubit in self.coupled_qubits
            },
            # 'ramsey_phases': {qubit: np.linspace(0.025, 0.025, 1) for qubit in  self.coupled_qubits},
        }
        # self.validate()


class ResetCalibrationSSRONode(BaseNode):
    measurement_obj = Reset_calibration_SSRO
    analysis_obj = ResetCalibrationSSRONodeAnalysis

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = couplers[0]
        self.coupled_qubits = couplers[0].split(sep="_")
        # self.schedule_keywords = kwargs
        self.redis_field = [
            "reset_fidelity",
            "reset_leakage",
            "all_fidelity",
            "all_fidelity_f",
        ]
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.
        self.dynamic = False
        self.schedule_keywords["swap_type"] = True
        self.schedule_samplespace = {
            "control_ons": {qubit: [False, True] for qubit in self.coupled_qubits},
            "ramsey_phases": {qubit: range(9) for qubit in self.coupled_qubits},
        }

