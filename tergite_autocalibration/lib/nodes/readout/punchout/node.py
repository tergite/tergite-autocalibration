import numpy as np

from tergite_autocalibration.utils.user_input import resonator_samples
from .analysis import PunchoutAnalysis
from .measurement import Punchout
from ....base.node import BaseNode


class Punchout_Node(BaseNode):
    measurement_obj = Punchout
    analysis_obj = PunchoutAnalysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.redis_field = ["measure:pulse_amp"]

        self.schedule_samplespace = {
            "ro_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            },
            "ro_amplitudes": {
                qubit: np.linspace(0.008, 0.06, 5) for qubit in self.all_qubits
            },
        }
