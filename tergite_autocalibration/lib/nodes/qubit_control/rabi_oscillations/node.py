# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Amr Osman 2024
# (C) Copyright Michele Faucci Giannelli 2024
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

from tergite_autocalibration.lib.base.node import QubitNode
from tergite_autocalibration.lib.nodes.qubit_control.rabi_oscillations.analysis import (
    NRabi_12_NodeAnalysis,
    NRabiNodeAnalysis,
    RabiNode12Analysis,
    RabiNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.qubit_control.rabi_oscillations.measurement import (
    NRabiOscillationsMeasurement,
    RabiOscillationsMeasurement,
)
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode
from tergite_autocalibration.lib.utils.analysis_models import RabiModel

rabi = RabiModel()


class RabiOscillationsBase(QubitNode):

    def __init__(self, all_qubits: list[str], couplers: list[str], **schedule_keywords):
        super().__init__(all_qubits, couplers, **schedule_keywords)

    def generate_dummy_dataset(self):
        dataset = xarray.Dataset()
        for index, qubit in enumerate(self.all_qubits):
            samples = self.schedule_samplespace["mw_amplitudes"][qubit]
            true_params = rabi.make_params(amplitude=0.2, frequency=1, offset=0.2)
            number_of_samples = len(samples)
            true_s21 = rabi.eval(params=true_params, drive_amp=samples)
            noise_scale = 0.005 * index
            np.random.seed(123)
            measured_s21 = np.abs(true_s21)
            measured_s21 = true_s21 + noise_scale * (
                np.random.randn(number_of_samples)
                + 1j * np.random.randn(number_of_samples)
            )
            data_array = xarray.DataArray(measured_s21)
            dataset[index] = data_array
        return dataset


class RabiOscillationsNode(RabiOscillationsBase):
    name: str = "rabi_oscillations"
    measurement_obj = RabiOscillationsMeasurement
    analysis_obj = RabiNodeAnalysis
    measurement_type = ScheduleNode

    qubit_qois = ["rxy:amp180"]

    def __init__(self, all_qubits: list[str], couplers: list[str], **schedule_keywords):
        super().__init__(all_qubits, couplers, **schedule_keywords)
        self.schedule_samplespace = {
            "mw_amplitudes": {
                qubit: np.linspace(0.002, 0.90, 61) for qubit in self.all_qubits
            }
        }


class RabiOscillations12Node(RabiOscillationsBase):
    name: str = "rabi_oscillations_12"
    measurement_obj = RabiOscillationsMeasurement
    analysis_obj = RabiNode12Analysis
    measurement_type = ScheduleNode
    qubit_qois = ["r12:ef_amp180"]

    def __init__(self, all_qubits: list[str], couplers: list[str], **schedule_keywords):
        super().__init__(all_qubits, couplers, **schedule_keywords)
        self.qubit_state = 1
        self.schedule_keywords["qubit_state"] = self.qubit_state

        self.schedule_samplespace = {
            "mw_amplitudes": {
                qubit: np.linspace(0.002, 0.800, 61) for qubit in self.all_qubits
            }
        }


class NRabiOscillationsNode(QubitNode):
    name: str = "n_rabi_oscillations"
    measurement_obj = NRabiOscillationsMeasurement
    analysis_obj = NRabiNodeAnalysis
    measurement_type = ScheduleNode
    qubit_qois = ["rxy:amp180"]

    def __init__(self, all_qubits: list[str], couplers: list[str], **schedule_keywords):
        super().__init__(all_qubits, couplers, **schedule_keywords)
        self.qubit_state = 0
        self.schedule_keywords["qubit_state"] = self.qubit_state

        self.schedule_samplespace = {
            "mw_amplitudes_sweep": {
                qubit: np.linspace(-0.045, 0.045, 30) for qubit in self.all_qubits
            },
            "X_repetitions": {qubit: np.arange(1, 23, 6) for qubit in self.all_qubits},
        }

    def generate_dummy_dataset(self):
        dataset = xarray.Dataset()
        real_correction = -0.01
        first_qubit = self.all_qubits[0]
        x_repetitions = self.schedule_samplespace["X_repetitions"][first_qubit]
        for index, _ in enumerate(self.all_qubits):
            data_array = np.array([])
            # TODO: the oscillations frequecny should be no set empirically
            for number_of_Xs in x_repetitions:
                this_frequency = 2 * number_of_Xs
                # find the phase that produces minimum at the real_correction
                this_phase = np.pi - 2 * np.pi * this_frequency * real_correction
                true_params = rabi.make_params(
                    amplitude=0.2,
                    frequency=this_frequency,
                    offset=0.2,
                    phase=this_phase,
                )
                samples = self.schedule_samplespace["mw_amplitudes_sweep"][first_qubit]
                number_of_samples = len(samples)
                fit_samples = np.linspace(samples[0], samples[-1], number_of_samples)
                true_s21 = rabi.eval(params=true_params, drive_amp=fit_samples)
                noise_scale = 0.02

                np.random.seed(123)
                measured_s21 = true_s21 + 0 * noise_scale * (
                    np.random.randn(number_of_samples)
                    + 1j * np.random.randn(number_of_samples)
                )
                data_array = np.concatenate((data_array, measured_s21))

            # Add the DataArray to the Dataset with an integer name (converted to string)
            dataset[index] = xarray.DataArray(data_array)
        return dataset


class NRabiOscillations12Node(QubitNode):
    name: str = "n_rabi_12_oscillations"
    measurement_obj = NRabiOscillationsMeasurement
    analysis_obj = NRabi_12_NodeAnalysis
    measurement_type = ScheduleNode
    qubit_qois = ["r12:ef_amp180"]

    def __init__(self, all_qubits: list[str], couplers: list[str], **schedule_keywords):
        super().__init__(all_qubits, couplers, **schedule_keywords)
        self.qubit_state = 1
        self.schedule_keywords["qubit_state"] = self.qubit_state

        self.schedule_samplespace = {
            "mw_amplitudes_sweep": {
                qubit: np.linspace(-0.05, 0.05, 51) for qubit in self.all_qubits
            },
            "X_repetitions": {qubit: np.arange(1, 8, 2) for qubit in self.all_qubits},
        }
