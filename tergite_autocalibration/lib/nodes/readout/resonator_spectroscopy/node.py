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

<<<<<<< HEAD
import numpy as np
import xarray
from quantify_core.analysis import fitting_models as fm

from tergite_autocalibration.config.VNA_values import VNA_resonator_frequencies
from tergite_autocalibration.lib.base.schedule_node import ScheduleNode
=======
>>>>>>> eleftherios/fix/fix-ro-amplitude-optimizations
from tergite_autocalibration.lib.nodes.readout.resonator_spectroscopy.analysis import (
    ResonatorSpectroscopy1NodeAnalysis,
    ResonatorSpectroscopy2NodeAnalysis,
    ResonatorSpectroscopyNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.readout.resonator_spectroscopy.measurement import (
    ResonatorSpectroscopyMeasurement,
)
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode

# TODO: check location
from tergite_autocalibration.lib.utils.samplespace import resonator_samples


<<<<<<< HEAD
class Resonator_Spectroscopy_Base(ScheduleNode):
    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)

        self.schedule_samplespace = {
            "ro_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }


class Resonator_Spectroscopy_Node(ScheduleNode):
    measurement_obj = Resonator_Spectroscopy
=======
class ResonatorSpectroscopyNode(ScheduleNode):
    measurement_obj = ResonatorSpectroscopyMeasurement
>>>>>>> eleftherios/fix/fix-ro-amplitude-optimizations
    analysis_obj = ResonatorSpectroscopyNodeAnalysis
    qubit_qois = ["clock_freqs:readout", "Ql", "resonator_minimum"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)

        self.schedule_samplespace = {
            "ro_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }

    def generate_dummy_dataset(self):
        dataset = xarray.Dataset()
        resonator = fm.ResonatorModel()
        for index, qubit in enumerate(self.all_qubits):
            ro_freq = VNA_resonator_frequencies[qubit]
            # if qubit == 'q02':
            #     ro_freq = ro_freq + 10e6
            true_params = resonator.make_params(
                fr=ro_freq,
                Ql=15000,
                Qe=20000,
                A=0.01,
                theta=0.5,
                phi_v=0,
                phi_0=0,
                # f_0=ro_freq, Q=10000, Q_e_real=9000, Q_e_imag=-9000
            )
            samples = resonator_samples(qubit)
            number_of_samples = len(samples)
            frequncies = np.linspace(samples[0], samples[-1], number_of_samples)
            true_s21 = resonator.eval(params=true_params, f=frequncies)
            noise_scale = 0.0001
            np.random.seed(123)
            measured_s21 = true_s21 + 1 * noise_scale * (
                np.random.randn(number_of_samples)
                + 1j * np.random.randn(number_of_samples)
            )
            data_array = xarray.DataArray(measured_s21)
            dataset[index] = data_array
        return dataset


class ResonatorSpectroscopy1Node(ScheduleNode):
    measurement_obj = ResonatorSpectroscopyMeasurement
    analysis_obj = ResonatorSpectroscopy1NodeAnalysis
    qubit_qois = [
        "extended_clock_freqs:readout_1",
        "Ql_1",
        "resonator_minimum_1",
    ]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.qubit_state = 1
        self.schedule_keywords["qubit_state"] = self.qubit_state

        self.schedule_samplespace = {
            "ro_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }


class ResonatorSpectroscopy2Node(ScheduleNode):
    measurement_obj = ResonatorSpectroscopyMeasurement
    analysis_obj = ResonatorSpectroscopy2NodeAnalysis
    qubit_qois = ["extended_clock_freqs:readout_2"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.qubit_state = 2
        self.schedule_keywords["qubit_state"] = self.qubit_state

        self.schedule_samplespace = {
            "ro_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }
