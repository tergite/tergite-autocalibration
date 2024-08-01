import numpy as np

from .analysis import (
    CZCalibrationAnalysis,
    CZCalibrationSSROAnalysis,
    ResetCalibrationSSROAnalysis,
)
from .measurement import (
    CZ_calibration,
    CZ_calibration_SSRO,
    Reset_calibration_SSRO,
)
from ....base.node import BaseNode


class CZ_Calibration_Node(BaseNode):
    measurement_obj = CZ_calibration
    analysis_obj = CZCalibrationAnalysis

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.coupled_qubits = couplers[0].split(sep="_")
        self.redis_field = ["cz_phase", "cz_pop_loss"]
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.
        self.schedule_keywords = schedule_keywords
        self.schedule_keywords["dynamic"] = False
        self.schedule_keywords["swap_type"] = False

        self.schedule_samplespace = {
            "ramsey_phases": {
                qubit: np.append(np.linspace(0, 360, 25), [0, 1])
                for qubit in self.coupled_qubits
            },
            "control_ons": {qubit: [False, True] for qubit in self.coupled_qubits},
        }


class CZ_Calibration_SSRO_Node(BaseNode):
    measurement_obj = CZ_calibration_SSRO
    analysis_obj = CZCalibrationSSROAnalysis

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
                coupler: np.append(np.linspace(0, 720, 25), [0, 1, 2]) for coupler in self.couplers
            },
        }

class CZ_Calibration_Swap_Node(BaseNode):
    measurement_obj = CZ_calibration
    analysis_obj = CZCalibrationAnalysis

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.coupled_qubits = couplers[0].split(sep="_")
        self.redis_field = ["cz_phase", "cz_pop_loss"]
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.

        self.schedule_keywords["dynamic"] = False
        self.schedule_keywords["swap_type"] = True
        self.schedule_samplespace = {
            "ramsey_phases": {
                qubit: np.append(np.linspace(0, 360, 25), [0, 1])
                for qubit in self.coupled_qubits
            },
            "control_ons": {qubit: [False, True] for qubit in self.coupled_qubits},
        }
        # self.schedule_keywords['use_edge'] = False
        # self.schedule_keywords['number_of_cz'] = 1
        # self.validate()


class CZ_Calibration_Swap_SSRO_Node(BaseNode):
    measurement_obj = CZ_calibration_SSRO
    analysis_obj = CZCalibrationSSROAnalysis

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.coupler = couplers[0]
        self.coupled_qubits = couplers[0].split(sep="_")
        # self.schedule_keywords = kwargs
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


class Reset_Calibration_SSRO_Node(BaseNode):
    measurement_obj = Reset_calibration_SSRO
    analysis_obj = ResetCalibrationSSROAnalysis

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = couplers[0]
        # print(couplers)
        self.coupled_qubits = couplers[0].split(sep="_")
        # print(self.coupled_qubits)
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
        # self.validate()
