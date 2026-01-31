# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024, 2025
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Amr Osman, 2024
# (C) Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from typing import Literal

import numpy as np
import xarray as xr
from scipy.stats import multivariate_normal

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.lib.base.node import CouplerNode
from tergite_autocalibration.lib.nodes.coupler.cz_parametrization.analysis import (
    CZParametrizationNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrization.measurement import (
    CZParametrizationMeasurement,
)
from tergite_autocalibration.lib.nodes.external_parameter_node import (
    ExternalParameterNode,
)
from tergite_autocalibration.lib.utils.classification_functions import generate_iq_shots


class CZParametrizationNode(CouplerNode):
    measurement_obj = CZParametrizationMeasurement
    analysis_obj = CZParametrizationNodeAnalysis
    measurement_type = ExternalParameterNode
    coupler_qois = ["cz_pulse_frequency", "cz_pulse_amplitude", "parking_current"]

    def __init__(self, name: str, all_qubits: list[str], couplers: list[str]):
        super().__init__(name, couplers)
        self.couplers = couplers

        self.coupled_qubits = self.get_coupled_qubits()
        self.all_qubits = self.coupled_qubits
        self.validate()

        self.schedule_keywords["loop_repetitions"] = 128
        self.loops = self.schedule_keywords["loop_repetitions"]
        self.ramp_back_to_zero = False
        phase_paths = self.all_phase_paths()
        self.analysis_keywords = {
            coupler: {"phase_path": phase_paths[coupler]} for coupler in self.couplers
        }

        self.external_samplespace = {
            "dc_currents": {
                coupler: self.fine_samplespace_around(self.parking_current(coupler))
                for coupler in self.couplers
            },
        }
        self.schedule_samplespace = {
            "cz_pulse_amplitudes": {
                coupler: np.linspace(0.15, 0.35, 25) for coupler in self.couplers
            },
            "cz_pulse_frequencies": {
                coupler: np.linspace(-7e6, 5e6, 25)
                + self.transition_frequency(coupler, phase_path=phase_paths[coupler])
                for coupler in self.couplers
            },
        }

    def fine_samplespace_around(self, central_value: float) -> np.ndarray:
        return np.arange(central_value - 5e-6, central_value + 4.5e-6, 13e-6)

    def broad_samplespace_around(self, central_value: float) -> np.ndarray:
        return np.arange(central_value - 50e-6, central_value + 45e-6, 8e-6)

    def parking_current(self, coupler: str):
        return float(REDIS_CONNECTION.hget(f"couplers:{coupler}", "parking_current"))

    def all_phase_paths(self) -> dict[str, Literal["via_02", "via_20"]]:
        phase_paths = {}
        for coupler in self.couplers:
            path = REDIS_CONNECTION.hget(f"couplers:{coupler}", "cz_phase_path")
            phase_paths[coupler] = path
        return phase_paths

    def initial_operation(self):
        pass

    def pre_measurement_operation(self, reduced_ext_space):
        iteration_dict = reduced_ext_space["dc_currents"]
        # there is some redundancy tha all qubits have the same
        # iteration index, that's why we keep the first value->
        this_iteration_value = list(iteration_dict.values())[0]
        dac_values = {}
        for coupler in self.couplers:
            this_iteration_value = iteration_dict[coupler]
            dac_values[coupler] = this_iteration_value
        self.spi_manager.set_dac_current(dac_values)

    def final_operation(self):
        """
        bring the current back to zero
        """
        if self.ramp_back_to_zero:
            dac_values = {}
            for coupler in self.couplers:
                dac_values[coupler] = 0
            self.spi_manager.set_dac_current(dac_values)

    def generate_dummy_dataset(self):
        dataset = xr.Dataset()
        for index, coupler in enumerate(self.couplers):
            q1, q2 = coupler.split("_")
            amplitudes = self.schedule_samplespace["cz_pulse_amplitudes"][coupler]
            frequencies = self.schedule_samplespace["cz_pulse_frequencies"][coupler]
            number_of_amplitudes = len(amplitudes)
            number_of_frequencies = len(frequencies)
            number_of_iq_samples = (
                number_of_amplitudes * number_of_frequencies * self.loops
            )

            # a simple 2d gaussian
            cov = np.array([[1, 0], [0, 1]])
            distr = multivariate_normal(cov=cov, mean=np.array([0, 0]))

            # Create a coordinate grid
            sigma_1, sigma_2 = cov[0, 0], cov[1, 1]
            x = np.linspace(-3 * sigma_1, 3 * sigma_1, num=number_of_frequencies)
            y = np.linspace(-3 * sigma_2, 3 * sigma_2, num=number_of_amplitudes)
            X, Y = np.meshgrid(x, y)

            # Generating the density function
            # for each point in the meshgrid
            pdf = np.zeros(X.shape)
            for i in range(X.shape[0]):
                for j in range(X.shape[1]):
                    pdf[i, j] = distr.pdf([X[i, j], Y[i, j]])

            # normalize
            pdf /= pdf.max()

            # emulate blobs
            peaks = pdf
            dips = 1 - pdf
            zeros = np.zeros((number_of_amplitudes, number_of_frequencies))

            complex_points_q1 = generate_iq_shots(
                np.array([peaks, dips, zeros]), q1, self.loops
            )
            complex_points_q2 = generate_iq_shots(
                np.array([zeros, dips, peaks]), q2, self.loops
            )
            data_array_q1 = xr.DataArray(complex_points_q1)
            data_array_q2 = xr.DataArray(complex_points_q2)

            dataset[2 * index] = data_array_q1
            dataset[2 * index + 1] = data_array_q2
        return dataset
