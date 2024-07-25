import numpy as np

from .analysis import MotzoiAnalysis
from .measurement import Motzoi_parameter
from ....base.node import BaseNode


class Motzoi_Parameter_Node(BaseNode):
    measurement_obj = Motzoi_parameter
    analysis_obj = MotzoiAnalysis

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ["rxy:motzoi"]
        self.backup = False
        self.motzoi_minima = []
        self.qubit_state = 0
        self.schedule_samplespace = {
            "mw_motzois": {
                qubit: np.linspace(-0.4, 0.1, 51) for qubit in self.all_qubits
            },
            "X_repetitions": {qubit: np.arange(1, 19, 6) for qubit in self.all_qubits},
        }
