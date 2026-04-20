# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024, 2025
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
import xarray
from lmfit.models import LorentzianModel

from tergite_autocalibration.config.globals import CONFIG
from tergite_autocalibration.lib.base.node import QubitNode
from tergite_autocalibration.lib.nodes.qubit_control.spectroscopy.analysis import (
    QubitSpectroscopy12NodeAnalysis,
    QubitSpectroscopyNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.qubit_control.spectroscopy.measurement import (
    TwoTonesAmplitudeMeasurement,
    TwoTonesMultidimMeasurement,
)
from tergite_autocalibration.lib.nodes.schedule_node import (
    OuterScheduleNode,
    ScheduleNode,
)
from tergite_autocalibration.lib.utils.samplespace import qubit_samples

peak = LorentzianModel()


class QubitSpectroscopyBase(QubitNode):

    def __init__(self, all_qubits: list[str], couplers: list[str], **schedule_keywords):
        super().__init__(all_qubits, couplers, **schedule_keywords)

    def generate_dummy_dataset(self):
        dataset = xarray.Dataset()
        first_qubit = self.all_qubits[0]
        number_of_amplitudes = len(
            self.schedule_samplespace["spec_pulse_amplitudes"][first_qubit]
        )
        for index, qubit in enumerate(self.all_qubits):
            qubit_freq = CONFIG.device.qubits[qubit]["VNA_f01_frequency"]
            samples = qubit_samples(qubit)
            if self.name == "qubit_12_spectroscopy":
                qubit_freq = CONFIG.device.qubits[qubit]["VNA_f12_frequency"]
                samples = qubit_samples(qubit, transition="12")
            true_params = peak.make_params(
                amplitude=0.2, center=qubit_freq, sigma=0.1e6
            )
            number_of_samples = len(samples)
            frequncies = np.linspace(samples[0], samples[-1], number_of_samples)
            true_s21 = peak.eval(params=true_params, x=frequncies)
            noise_scale = 0.02

            np.random.seed(123)
            measured_s21 = true_s21 + 0 * noise_scale * (
                np.random.randn(number_of_samples)
                + 1j * np.random.randn(number_of_samples)
            )
            measured_s21 = np.repeat(measured_s21, number_of_amplitudes)
            data_array = xarray.DataArray(measured_s21)

            # Add the DataArray to the Dataset with an integer name (converted to string)
            dataset[index] = data_array
        return dataset


class Qubit01SpectroscopyNode(QubitSpectroscopyBase):
    name: str = "qubit_01_spectroscopy"
    measurement_obj = TwoTonesMultidimMeasurement
    analysis_obj = QubitSpectroscopyNodeAnalysis
    measurement_type = ScheduleNode
    qubit_qois = ["clock_freqs:f01", "spec:spec_ampl_optimal"]

    def __init__(self, all_qubits: list[str], couplers: list[str], **schedule_keywords):
        super().__init__(all_qubits, couplers, **schedule_keywords)

        self.schedule_samplespace = {
            "spec_pulse_amplitudes": {
                qubit: np.linspace(1e-3, 8e-3, 5) for qubit in self.all_qubits
            },
            "spec_frequencies": {
                qubit: qubit_samples(qubit) for qubit in self.all_qubits
            },
        }


class Qubit12SpectroscopyNode(QubitSpectroscopyBase):
    name: str = "qubit_12_spectroscopy"
    measurement_obj = TwoTonesMultidimMeasurement
    analysis_obj = QubitSpectroscopy12NodeAnalysis
    measurement_type = ScheduleNode
    qubit_qois = ["clock_freqs:f12", "spec:spec_ampl_12_optimal"]

    def __init__(self, all_qubits: list[str], couplers: list[str], **schedule_keywords):
        super().__init__(all_qubits, couplers, **schedule_keywords)
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


class Qubit01SpectroscopyAmplitudeNode(QubitNode):
    name: str = "qubit_bring_up_spectroscopy"
    measurement_obj = TwoTonesAmplitudeMeasurement
    analysis_obj = QubitSpectroscopyNodeAnalysis
    measurement_type = OuterScheduleNode
    qubit_qois = ["clock_freqs:f01", "spec:spec_ampl_optimal"]

    def __init__(self, all_qubits: list[str], couplers: list[str], **schedule_kwargs):
        super().__init__(all_qubits, couplers, **schedule_kwargs)

        self.outer_schedule_samplespace = {
            "spec_pulse_amplitudes": {
                qubit: np.linspace(8e-3, 8e-2, 2) for qubit in self.all_qubits
            },
        }

        self.schedule_samplespace = {
            "spec_frequencies": {
                qubit: self.qubit_samples(qubit) for qubit in self.all_qubits
            },
        }

    def qubit_samples(self, qubit: str) -> np.ndarray:
        qub_spec_samples = 821
        sweep_range = 500e6
        VNA_frequency = CONFIG.device.qubits[qubit]["VNA_f01_frequency"]
        min_freq = VNA_frequency - sweep_range / 2 + 0 * 50e6
        max_freq = VNA_frequency + sweep_range / 2 + 0 * 50e6
        return np.linspace(min_freq, max_freq, qub_spec_samples)
