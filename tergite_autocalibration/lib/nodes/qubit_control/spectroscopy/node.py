import numpy as np
from qblox_instruments import Cluster

from tergite_autocalibration.lib.nodes.qubit_control.spectroscopy.qubit_spectroscopy_analysis import QubitSpectroscopyAnalysis
from tergite_autocalibration.lib.nodes.qubit_control.spectroscopy.qubit_spectroscopy_multidim import QubitSpectroscopyMultidim
from tergite_autocalibration.lib.base.node import BaseNode
from tergite_autocalibration.lib.nodes.qubit_control.qubit_spectroscopy.cw_two_nones_spectroscopy import CW_Two_Tones_Spectroscopy
from tergite_autocalibration.lib.nodes.qubit_control.qubit_spectroscopy.two_tone_multidim import Two_Tones_Multidim
from tergite_autocalibration.utils.hardware_utils import set_qubit_LO
from tergite_autocalibration.utils.user_input import qubit_samples


class Qubit_01_Spectroscopy_CW_Node(BaseNode):
    measurement_obj = CW_Two_Tones_Spectroscopy
    analysis_obj = QubitSpectroscopyMultidim

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.sweep_range = self.node_dictionary.pop("sweep_range", None)
        self.redis_field = ["clock_freqs:f01"]

        self.operations_args = []

        self.external_samplespace = {
            "cw_frequencies": {qubit: qubit_samples(qubit) for qubit in self.all_qubits}
        }

    def pre_measurement_operation(self, reduced_ext_space):
        settable = list(reduced_ext_space.keys())[0]
        for instrument in self.lab_instr_coordinator.values():
            if type(instrument) == Cluster:
                cluster = instrument
        for qubit in self.all_qubits:
            lo_frequency = reduced_ext_space[settable][qubit]
            set_qubit_LO(cluster, qubit, lo_frequency)


class Qubit_01_Spectroscopy_Multidim_Node(BaseNode):
    measurement_obj = Two_Tones_Multidim
    analysis_obj = QubitSpectroscopyMultidim

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ["clock_freqs:f01", "spec:spec_ampl_optimal"]

        self.schedule_samplespace = {
            "spec_pulse_amplitudes": {
                qubit: np.linspace(4e-4, 8e-3, 5) for qubit in self.all_qubits
            },
            "spec_frequencies": {
                qubit: qubit_samples(qubit) for qubit in self.all_qubits
            },
        }


class Qubit_12_Spectroscopy_Pulsed_Node(BaseNode):
    measurement_obj = Two_Tones_Multidim
    analysis_obj = QubitSpectroscopyAnalysis

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.sweep_range = self.node_dictionary.pop("sweep_range", None)
        self.redis_field = ["clock_freqs:f12"]
        self.qubit_state = 1

        self.schedule_samplespace = {
            "spec_frequencies": {
                qubit: qubit_samples(qubit, "12", sweep_range=self.sweep_range)
                for qubit in self.all_qubits
            }
        }


class Qubit_12_Spectroscopy_Multidim_Node(BaseNode):
    measurement_obj = Two_Tones_Multidim
    analysis_obj = QubitSpectroscopyMultidim

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ["clock_freqs:f12", "spec:spec_ampl_12_optimal"]
        self.qubit_state = 1

        self.schedule_samplespace = {
            "spec_pulse_amplitudes": {
                qubit: np.linspace(6e-3, 3e-2, 3) for qubit in self.all_qubits
            },
            "spec_frequencies": {
                qubit: qubit_samples(qubit, transition="12")
                for qubit in self.all_qubits
            },
        }
