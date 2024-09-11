import numpy as np

from .analysis import (
    ProcessTomographyAnalysis,
)
from .measurement import (
    Process_Tomography,
)
from ....base.node import BaseNode


class Process_Tomography_Node(BaseNode):
    measurement_obj = Process_Tomography
    analysis_obj = ProcessTomographyAnalysis

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary
    ):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = couplers[0]
        # print(couplers)
        self.coupled_qubits = couplers[0].split(sep="_")
        # print(self.coupled_qubits)
        # self.node_dictionary = kwargs
        self.redis_field = [
            "pop_g",
            "pop_e",
            "pop_f",
        ]
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.
        self.schedule_samplespace = {
            "control_ons": {coupler: range(9) for coupler in self.couplers},
            "ramsey_phases": {
                coupler: np.append(range(16), [0, 1, 2]) for coupler in self.couplers
            },
        }
        # self.validate()
