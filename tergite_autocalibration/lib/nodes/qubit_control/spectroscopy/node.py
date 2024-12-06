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

import numpy as np

from tergite_autocalibration.lib.nodes.qubit_control.spectroscopy.analysis import (
    QubitSpectroscopyNodeAnalysis,
    QubitSpectroscopyNodeMultidim,
)
from tergite_autocalibration.lib.nodes.qubit_control.spectroscopy.measurement import (
    Two_Tones_Multidim,
)
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode
# TODO: check input
from tergite_autocalibration.utils.user_input import qubit_samples


class Qubit_01_Spectroscopy_Multidim_Node(ScheduleNode):
    measurement_obj = Two_Tones_Multidim
    analysis_obj = QubitSpectroscopyNodeMultidim
    qubit_qois = ["clock_freqs:f01", "spec:spec_ampl_optimal"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)

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

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.qubit_state = 1
        self.schedule_keywords["qubit_state"] = self.qubit_state

        self.schedule_samplespace = {
            "spec_frequencies": {
                qubit: qubit_samples(qubit, "12") for qubit in self.all_qubits
            }
        }


class Qubit_12_Spectroscopy_Multidim_Node(ScheduleNode):
    measurement_obj = Two_Tones_Multidim
    analysis_obj = QubitSpectroscopyNodeMultidim
    qubit_qois = ["clock_freqs:f12", "spec:spec_ampl_12_optimal"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.qubit_state = 1
        self.schedule_keywords["qubit_state"] = self.qubit_state

        self.schedule_samplespace = {
            "spec_pulse_amplitudes": {
                qubit: np.linspace(6e-3, 3e-2, 3) for qubit in self.all_qubits
            },
            "spec_frequencies": {
                qubit: qubit_samples(qubit, transition="12")
                for qubit in self.all_qubits
            },
        }
