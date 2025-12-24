# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024, 2025
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import xarray
import numpy as np
from quantify_core.analysis import fitting_models as fm
from tergite_autocalibration.lib.base.node import QubitNode
from tergite_autocalibration.lib.nodes.readout.resonator_spectroscopy.analysis import (
    ResonatorSpectroscopy1NodeAnalysis,
    ResonatorSpectroscopy2NodeAnalysis,
    ResonatorSpectroscopyNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.readout.resonator_spectroscopy.measurement import (
    ResonatorSpectroscopyMeasurement,
)

from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode
from tergite_autocalibration.lib.utils.samplespace import resonator_samples
from tergite_autocalibration.config.legacy import dh


resonator = fm.ResonatorModel()


class ResonatorSpectroscopyBase(QubitNode):

    def __init__(self, name: str, all_qubits: list[str], couplers: list[str],  **schedule_keywords):
        super().__init__(name, all_qubits, couplers=couplers,  **schedule_keywords)
        self.name = name

    def generate_dummy_dataset(self, noise=False):
        dataset = xarray.Dataset()
        if self.name == "resonator_spectroscopy":
            frequency_shift = 0
        elif self.name == "resonator_spectroscopy_1":
            frequency_shift = 0.5e6
        elif self.name == "resonator_spectroscopy_2":
            frequency_shift = 1e6
        else:
            raise ValueError("Invalid name")

        for index, qubit in enumerate(self.all_qubits):
            vna_ro_freq = dh.get_legacy("VNA_resonator_frequencies")[qubit]
            ro_freq = vna_ro_freq - frequency_shift
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
            np.random.seed(123)
            samples = resonator_samples(qubit)
            number_of_samples = len(samples)
            frequncies = np.linspace(samples[0], samples[-1], number_of_samples)
            true_s21 = resonator.eval(params=true_params, f=frequncies)
            noise_scale = 0.02
            noise_s21 = noise_scale * (
                np.random.randn(number_of_samples)
                + 1j * np.random.randn(number_of_samples)
            )
            measured_s21 = true_s21
            if noise:
                measured_s21 += noise_s21
            data_array = xarray.DataArray(measured_s21)
            dataset[index] = data_array
        return dataset


class ResonatorSpectroscopyNode(ResonatorSpectroscopyBase):
    measurement_obj = ResonatorSpectroscopyMeasurement
    analysis_obj = ResonatorSpectroscopyNodeAnalysis
    measurement_type = ScheduleNode
    qubit_qois = ["clock_freqs:readout", "Ql", "resonator_minimum"]

    def __init__(self, name: str, all_qubits: list[str], **node_keywords):
        super().__init__(name, all_qubits, **node_keywords)

        self.schedule_samplespace = {
            "ro_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }


class ResonatorSpectroscopy1Node(ResonatorSpectroscopyBase):
    measurement_obj = ResonatorSpectroscopyMeasurement
    analysis_obj = ResonatorSpectroscopy1NodeAnalysis
    measurement_type = ScheduleNode
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


class ResonatorSpectroscopy2Node(ResonatorSpectroscopyBase):
    measurement_obj = ResonatorSpectroscopyMeasurement
    analysis_obj = ResonatorSpectroscopy2NodeAnalysis
    measurement_type = ScheduleNode
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
