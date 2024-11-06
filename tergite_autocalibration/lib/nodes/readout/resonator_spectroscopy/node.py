# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023
# (C) Copyright Michele Faucci Giannelli 2024
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

from .analysis import (
    ResonatorSpectroscopy1NodeAnalysis,
    ResonatorSpectroscopy2NodeAnalysis,
    ResonatorSpectroscopyNodeAnalysis,
)
from .measurement import Resonator_Spectroscopy

with open('./configs/VNA_values.json') as vna:
    VNA = json.load(vna)
VNA_resonator_frequencies = VNA['VNA_resonator_frequencies']


def resonator_samples(qubit: str) -> np.ndarray:
    res_spec_samples = 70
    sweep_range = 5.0e6
    VNA_frequency = VNA_resonator_frequencies[qubit]
    min_freq = VNA_frequency - sweep_range / 2
    max_freq = VNA_frequency + sweep_range / 2
    return np.linspace(min_freq, max_freq, res_spec_samples)


class Resonator_Spectroscopy_Node(ScheduleNode):
    measurement_obj = Resonator_Spectroscopy
    analysis_obj = ResonatorSpectroscopyNodeAnalysis
    qubit_qois = ["clock_freqs:readout", "Ql", "resonator_minimum"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)

        self.schedule_samplespace = {
            "ro_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }


class Resonator_Spectroscopy_1_Node(ScheduleNode):
    measurement_obj = Resonator_Spectroscopy
    analysis_obj = ResonatorSpectroscopy1NodeAnalysis
    qubit_qois = [
        "extended_clock_freqs:readout_1",
        "Ql_1",
        "resonator_minimum_1",
    ]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.qubit_state = 1

        self.schedule_samplespace = {
            "ro_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }


class Resonator_Spectroscopy_2_Node(ScheduleNode):
    measurement_obj = Resonator_Spectroscopy
    analysis_obj = ResonatorSpectroscopy2NodeAnalysis
    qubit_qois = ["extended_clock_freqs:readout_2"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.qubit_state = 2

        self.schedule_samplespace = {
            "ro_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }
