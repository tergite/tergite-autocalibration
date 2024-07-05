import numpy as np

from ..cz_calibration.analysis import (
    CZCalibrationAnalysis,
)
from ..cz_calibration.measurement import (
    CZ_calibration,
)
from ....base.node import BaseNode


class CZ_Dynamic_Phase_Node(BaseNode):
    measurement_obj = CZ_calibration
    analysis_obj = CZCalibrationAnalysis

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary
    ):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.coupled_qubits = couplers[0].split(sep="_")
        self.redis_field = ["cz_dynamic_target"]
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.
        self.node_dictionary["dynamic"] = True
        self.node_dictionary["swap_type"] = False
        self.node_dictionary["use_edge"] = False
        self.schedule_samplespace = {
            "ramsey_phases": {
                qubit: np.append(np.linspace(0, 360, 25), [0, 1])
                for qubit in self.coupled_qubits
            },
            "control_ons": {qubit: [False, True] for qubit in self.coupled_qubits},
        }


class CZ_Dynamic_Phase_Swap_Node(BaseNode):
    measurement_obj = CZ_calibration
    analysis_obj = CZCalibrationAnalysis

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary
    ):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.coupled_qubits = couplers[0].split(sep="_")
        self.redis_field = ["cz_dynamic_control"]
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.
        self.node_dictionary["dynamic"] = True
        self.node_dictionary["swap_type"] = True
        self.node_dictionary["use_edge"] = False
        self.schedule_samplespace = {
            "ramsey_phases": {
                qubit: np.append(np.linspace(0, 360, 25), [0, 1])
                for qubit in self.coupled_qubits
            },
            "control_ons": {qubit: [False, True] for qubit in self.coupled_qubits},
        }
