import numpy as np

from .analysis import All_XY_Analysis
from .measurement import All_XY
from ....base.node import BaseNode


class All_XY_Node(BaseNode):
    measurement_obj = All_XY
    analysis_obj = All_XY_Analysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.all_qubits = all_qubits
        self.redis_field = ["error_syndromes"]
        self.backup = False
        # TODO properly set the dimensions
        self.schedule_samplespace = {
            "XY_index": {qubit: np.array(range(23)) for qubit in self.all_qubits}
        }
