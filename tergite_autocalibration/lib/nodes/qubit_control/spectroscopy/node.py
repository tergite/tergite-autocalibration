# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import json
import numpy as np
from tergite_autocalibration.lib.base.schedule_node import ScheduleNode

from .analysis import QubitSpectroscopyNodeAnalysis, QubitSpectroscopyNodeMultidim
from .measurement import Two_Tones_Multidim

with open("./configs/VNA_values.json") as vna:
    VNA = json.load(vna)
VNA_qubit_frequencies = VNA["VNA_qubit_frequencies"]
VNA_f12_frequencies = VNA["VNA_f12_frequencies"]


def qubit_samples(qubit: str, transition: str = "01") -> np.ndarray:
    qub_spec_samples = 51
    sweep_range = 10e6
    if transition == "01":
        VNA_frequency = VNA_qubit_frequencies[qubit]
    elif transition == "12":
        VNA_frequency = VNA_f12_frequencies[qubit]
    min_freq = VNA_frequency - sweep_range / 2
    max_freq = VNA_frequency + sweep_range / 2
    return np.linspace(min_freq, max_freq, qub_spec_samples)


class Qubit_01_Spectroscopy_Multidim_Node(ScheduleNode):
    measurement_obj = Two_Tones_Multidim
    analysis_obj = QubitSpectroscopyNodeMultidim
    qubit_qois = ["clock_freqs:f01", "spec:spec_ampl_optimal"]

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)

        self.schedule_samplespace = {
            "spec_pulse_amplitudes": {
                qubit: np.linspace(4e-4, 8e-3, 5) for qubit in self.all_qubits
            },
            "spec_frequencies": {
                qubit: qubit_samples(qubit) for qubit in self.all_qubits
            },
        }


class Qubit_12_Spectroscopy_Pulsed_Node(ScheduleNode):
    measurement_obj = Two_Tones_Multidim
    analysis_obj = QubitSpectroscopyNodeAnalysis
    qubit_qois = ["clock_freqs:f12"]

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.qubit_state = 1

        self.schedule_samplespace = {
            "spec_frequencies": {
                qubit: qubit_samples(qubit, "12") for qubit in self.all_qubits
            }
        }


class Qubit_12_Spectroscopy_Multidim_Node(ScheduleNode):
    measurement_obj = Two_Tones_Multidim
    analysis_obj = QubitSpectroscopyNodeMultidim
    qubit_qois = ["clock_freqs:f12", "spec:spec_ampl_12_optimal"]

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
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
