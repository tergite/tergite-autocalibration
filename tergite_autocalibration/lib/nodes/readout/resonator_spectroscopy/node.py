from tergite_autocalibration.utils.user_input import resonator_samples
from .analysis import ResonatorSpectroscopyAnalysis, ResonatorSpectroscopy_1_Analysis, ResonatorSpectroscopy_2_Analysis
from .measurement import Resonator_Spectroscopy
from ....base.node import BaseNode


class Resonator_Spectroscopy_Node(BaseNode):
    measurement_obj = Resonator_Spectroscopy
    analysis_obj = ResonatorSpectroscopyAnalysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)

        self.redis_field = ["clock_freqs:readout", "Ql", "resonator_minimum"]
        self.schedule_samplespace = {
            "ro_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }


class Resonator_Spectroscopy_1_Node(BaseNode):
    measurement_obj = Resonator_Spectroscopy
    analysis_obj = ResonatorSpectroscopy_1_Analysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.redis_field = [
            "extended_clock_freqs:readout_1",
            "Ql_1",
            "resonator_minimum_1",
        ]
        self.qubit_state = 1

        self.schedule_samplespace = {
            "ro_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }


class Resonator_Spectroscopy_2_Node(BaseNode):
    measurement_obj = Resonator_Spectroscopy
    analysis_obj = ResonatorSpectroscopy_2_Analysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.redis_field = ["extended_clock_freqs:readout_2"]
        self.qubit_state = 2

        self.schedule_samplespace = {
            "ro_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }
