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
import xarray
from lmfit.models import LorentzianModel

from tergite_autocalibration.config.VNA_values import VNA_qubit_frequencies
from tergite_autocalibration.lib.base.schedule_node import ScheduleNode
from tergite_autocalibration.lib.nodes.qubit_control.spectroscopy.analysis import (
    QubitSpectroscopyNodeMultidim,
)
from tergite_autocalibration.lib.nodes.qubit_control.spectroscopy.measurement_ar import (
    Two_Tones_Multidim_AR,
)
from tergite_autocalibration.utils.user_input import qubit_samples


def interleave_zeros(arr: np.ndarray):
    # interleave dummy active reset aqcuisitions, the value=0 desn't matter
    new_array = np.zeros(2 * len(arr), dtype=arr.dtype)
    new_array[1::2] = arr
    return new_array


class Qubit_01_Spectroscopy_Multidim_AR_Node(ScheduleNode):
    measurement_obj = Two_Tones_Multidim_AR
    analysis_obj = QubitSpectroscopyNodeMultidim
    qubit_qois = ["clock_freqs:f01", "spec:spec_ampl_optimal"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_kwargs):
        super().__init__(name, all_qubits, **schedule_kwargs)
        self.is_ar = True

        self.schedule_samplespace = {
            "spec_pulse_amplitudes": {
                qubit: np.linspace(4e-3, 8e-3, 1) for qubit in self.all_qubits
            },
            "spec_frequencies": {
                qubit: qubit_samples(qubit) for qubit in self.all_qubits
            },
        }

    def generate_dummy_dataset(self):
        peak = LorentzianModel()
        dataset = xarray.Dataset()
        first_qubit = self.all_qubits[0]
        number_of_amplitudes = len(
            self.schedule_samplespace["spec_pulse_amplitudes"][first_qubit]
        )
        for index, qubit in enumerate(self.all_qubits):
            qubit_freq = VNA_qubit_frequencies[qubit]
            true_params = peak.make_params(
                amplitude=0.2, center=qubit_freq, sigma=0.3e6
            )
            samples = qubit_samples(qubit)
            number_of_samples = len(samples)
            frequncies = np.linspace(samples[0], samples[-1], number_of_samples)
            true_s21 = peak.eval(params=true_params, x=frequncies)
            noise_scale = 0.001

            np.random.seed(123)
            measured_s21 = true_s21 + 0 * noise_scale * (
                np.random.randn(number_of_samples)
                + 1j * np.random.randn(number_of_samples)
            )
            measured_s21 = np.repeat(measured_s21, number_of_amplitudes)
            measured_s21 = interleave_zeros(measured_s21)
            data_array = xarray.DataArray(measured_s21)

            # Add the DataArray to the Dataset with an integer name (converted to string)
            dataset[index] = data_array
        return dataset
