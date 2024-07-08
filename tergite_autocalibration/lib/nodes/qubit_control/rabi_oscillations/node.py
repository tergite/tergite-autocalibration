import numpy as np

from .analysis import RabiAnalysis, NRabiAnalysis
from .measurement import (
    Rabi_Oscillations,
    N_Rabi_Oscillations,
)
from ....base.node import BaseNode


class Rabi_Oscillations_Node(BaseNode):
    measurement_obj = Rabi_Oscillations
    analysis_obj = RabiAnalysis

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ["rxy:amp180"]
        self.schedule_samplespace = {
            "mw_amplitudes": {
                qubit: np.linspace(0.002, 0.90, 61) for qubit in self.all_qubits
            }
        }


class Rabi_Oscillations_12_Node(BaseNode):
    measurement_obj = Rabi_Oscillations
    analysis_obj = RabiAnalysis

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ["r12:ef_amp180"]
        self.qubit_state = 1

        self.schedule_samplespace = {
            "mw_amplitudes": {
                qubit: np.linspace(0.002, 0.800, 61) for qubit in self.all_qubits
            }
        }


class N_Rabi_Oscillations_Node(BaseNode):
    measurement_obj = N_Rabi_Oscillations
    analysis_obj = NRabiAnalysis

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ["rxy:amp180"]
        self.backup = False

        self.schedule_samplespace = {
            "mw_amplitudes_sweep": {
                qubit: np.linspace(-0.045, 0.045, 40) for qubit in self.all_qubits
            },
            "X_repetitions": {qubit: np.arange(1, 40, 8) for qubit in self.all_qubits},
        }
