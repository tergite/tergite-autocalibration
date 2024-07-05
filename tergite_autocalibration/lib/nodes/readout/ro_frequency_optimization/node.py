from tergite_autocalibration.utils.user_input import resonator_samples
from .analysis import OptimalROFrequencyAnalysis, OptimalRO_012_FrequencyAnalysis
from .measurement import RO_frequency_optimization
from ....base.node import BaseNode


class RO_frequency_two_state_optimization_Node(BaseNode):
    measurement_obj = RO_frequency_optimization
    analysis_obj = OptimalROFrequencyAnalysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.redis_field = ["extended_clock_freqs:readout_2state_opt"]
        self.qubit_state = 0

        self.schedule_samplespace = {
            "ro_opt_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            },
            "qubit_states": {qubit: [0, 1] for qubit in self.all_qubits},
        }


class RO_frequency_three_state_optimization_Node(BaseNode):
    measurement_obj = RO_frequency_optimization
    analysis_obj = OptimalRO_012_FrequencyAnalysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.all_qubits = all_qubits
        self.redis_field = ["extended_clock_freqs:readout_3state_opt"]
        self.qubit_state = 2

        self.schedule_samplespace = {
            "ro_opt_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            },
            "qubit_states": {qubit: [0, 1, 2] for qubit in self.all_qubits},
        }
