import numpy as np

from .analysis import RamseyDetuningsAnalysis
from .measurement import Ramsey_detunings
from ....base.node import BaseNode


class Ramsey_Fringes_12_Node(BaseNode):
    measurement_obj = Ramsey_detunings
    analysis_obj = RamseyDetuningsAnalysis

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ["clock_freqs:f12"]
        self.qubit_state = 1
        self.backup = False
        self.analysis_kwargs = {"redis_field": "clock_freqs:f12"}
        self.schedule_samplespace = {
            "ramsey_delays": {
                qubit: np.arange(4e-9, 2048e-9, 8 * 8e-9) for qubit in self.all_qubits
            },
            "artificial_detunings": {
                qubit: np.arange(-2.1, 2.1, 0.8) * 1e6 for qubit in self.all_qubits
            },
        }


class Ramsey_Fringes_Node(BaseNode):
    measurement_obj = Ramsey_detunings
    analysis_obj = RamseyDetuningsAnalysis

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ["clock_freqs:f01"]
        self.backup = False
        self.analysis_kwargs = {"redis_field": "clock_freqs:f01"}
        self.schedule_samplespace = {
            "ramsey_delays": {
                qubit: np.arange(4e-9, 2048e-9, 8 * 8e-9) for qubit in self.all_qubits
            },
            "artificial_detunings": {
                qubit: np.arange(-2.1, 2.1, 0.8) * 1e6 for qubit in self.all_qubits
            },
            # },
        }
