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

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from scipy.ndimage import convolve

from tergite_autocalibration.lib.base.analysis import (
    BaseAllCouplersAnalysis,
    BaseCouplerAnalysis,
)
from tergite_autocalibration.lib.utils.classification_functions import (
    calculate_probabilities,
)
from tergite_autocalibration.utils.dto.qoi import QOI


class CZParametrizationAnalysis(BaseCouplerAnalysis):

    def __init__(self, name, redis_fields, **kwargs):
        super().__init__(name, redis_fields)
        self.phase_path: Literal["via_20", "via_02"] = kwargs["phase_path"]

    def calculate_probabilities(self):
        dataset = self.S21
        for coord in dataset.coords:
            coord = str(coord)
            if "loops" in coord:
                self.loops_coord = coord
                self.number_of_loops = dataset[self.loops_coord].size
            elif "frequencies" in coord:
                self.frequencies_coord = coord
                self.frequencies = dataset[self.frequencies_coord].values
                self.number_of_frequencies = dataset[self.frequencies_coord].size
            elif "amplitudes" in coord:
                self.amplitudes_coord = coord
                self.amplitudes = dataset[self.amplitudes_coord].values
                self.x_coordinate = coord
            elif "durations" in coord:
                self.durations_coord = coord
                self.durations = dataset[self.durations_coord].values
                self.x_coordinate = coord
            elif "dc_currents" in coord:
                self.dc_currents_coord = coord
                self.dc_currents = dataset[self.dc_currents_coord].values
                self.number_of_dc_currents = dataset[self.dc_currents_coord].size

        control_qubit_probabilities = calculate_probabilities(
            self.control_qubit_data_var
        )
        target_qubit_probabilities = calculate_probabilities(self.target_qubit_data_var)

        self.probabilities = xr.concat(
            [control_qubit_probabilities, target_qubit_probabilities],
            dim="qubit",
        )
        self.probabilities = self.probabilities.rename(self.coupler)


class CZParametrizationCouplerAnalysis(CZParametrizationAnalysis):

    def __init__(self, name, redis_fields, **kwargs):
        super().__init__(name, redis_fields, **kwargs)

    def analyze_coupler(self):
        self.calculate_probabilities()

        self.optimal_values = xr.DataArray(name=self.coupler)
        for current_index, _ in enumerate(self.dc_currents):
            current_probabilities = self.probabilities.isel(
                {self.dc_currents_coord: current_index}
            )
            control_state_2 = current_probabilities.sel(
                {"qubit": self.control_qubit, "state": 2}
            )
            control_state_1 = current_probabilities.sel(
                {"qubit": self.control_qubit, "state": 1}
            )
            control_state_0 = current_probabilities.sel(
                {"qubit": self.control_qubit, "state": 0}
            )
            target_state_0 = current_probabilities.sel(
                {"qubit": self.target_qubit, "state": 0}
            )
            target_state_1 = current_probabilities.sel(
                {"qubit": self.target_qubit, "state": 1}
            )
            target_state_2 = current_probabilities.sel(
                {"qubit": self.target_qubit, "state": 2}
            )
            if self.phase_path == "via_20":
                control_diffs = control_state_2 - control_state_1 - control_state_0
                target_diffs = target_state_0 - target_state_1 - target_state_2
            elif self.phase_path == "via_02":
                control_diffs = control_state_0 - control_state_1 - control_state_2
                target_diffs = target_state_2 - target_state_1 - target_state_0
            else:
                raise ValueError("Invalid phase path")

            # Compute signed distance including nearest neighbor influence
            convolution_kernel = np.array(
                [[0.02, 0.05, 0.01], [0.05, 1.0, 0.05], [0.02, 0.02, 0.02]]
            )

            summed_differences = control_diffs + target_diffs

            weighted_sum = summed_differences.copy(deep=True)
            weighted_sum.values = convolve(
                weighted_sum.values,
                convolution_kernel / np.sum(convolution_kernel),
                mode="constant",
                cval=-1,
            )

            weighted_optimal_point = (
                weighted_sum.where(weighted_sum == weighted_sum.max(), drop=True)
                .expand_dims(self.dc_currents_coord)  # promote dimension
                .expand_dims({"index": [current_index]})
            )
            weighted_optimal_point = weighted_optimal_point.stack(
                multi=[
                    self.frequencies_coord,
                    self.amplitudes_coord,
                    self.dc_currents_coord,
                    "index",
                ]
            )
            self.optimal_values = xr.merge(
                [self.optimal_values, weighted_optimal_point],
                join="outer",
                compat="no_conflicts",
            )

        optimal_coords = self.optimal_values.idxmax()
        self.optimal_frequency = optimal_coords[self.coupler].values.tolist()[0]
        self.optimal_amplitude = optimal_coords[self.coupler].values.tolist()[1]
        self.optimal_dc_current = optimal_coords[self.coupler].values.tolist()[2]
        self.optimal_current_index = optimal_coords[self.coupler].values.tolist()[3]

        self.analysis_succesful = any(self.optimal_values[self.coupler] > 1)
        analysis_result = {
            "cz_pulse_frequency": {
                "value": self.optimal_frequency,
                "error": 0,
            },
            "cz_pulse_amplitude": {
                "value": self.optimal_amplitude,
                "error": 0,
            },
            "parking_current": {
                "value": self.optimal_dc_current,
                "error": 0,
            },
        }
        qoi = QOI(analysis_result, self.analysis_succesful)
        return qoi

    @property
    def processed_dataset(self):
        return self.probabilities

    def plotter(self, figures_dictionary: dict[str, list]):
        figures_list = []
        for current_index, current in enumerate(self.dc_currents):

            marker = "8"
            if current_index == self.optimal_current_index:
                marker = "*"
            current_probabilities = self.probabilities.isel(
                {self.dc_currents_coord: current_index}
            )

            current_probabilities.plot(
                x=self.frequencies_coord,
                cmap="RdBu_r",
                row="qubit",
                col="state",
            )

            population_exchange_points = self.optimal_values.sel(
                {"index": current_index}
            )
            frequency = population_exchange_points[self.frequencies_coord]
            amplitude = population_exchange_points[self.amplitudes_coord]
            score = population_exchange_points[self.coupler].item()
            fig = plt.gcf()

            if self.analysis_succesful:
                title = f"{score = :.3f}   {current = :.6f}"
                fig.suptitle(title, x=0.55, color="red")
                for ax in fig.axes:
                    ax.scatter(
                        frequency,
                        amplitude,
                        s=100,
                        color="yellow",
                        marker=marker,
                    )
                if current_index == self.optimal_current_index:
                    fig.suptitle(
                        f"{current = :.6f}"
                        f"  score = {score:.3f}"
                        f"  freq = {self.optimal_frequency:.5e}"
                        f"  ampl = {self.optimal_amplitude:.5f}",
                        x=0.5,
                        size=14,
                        color="red",
                    )
            else:
                title = f"No good points found, {score = :.3f}   {current = :.6f}"
                fig.suptitle(title, x=0.55, color="red")
            figures_list.append(fig)

        figures_dictionary[self.coupler] = figures_list


class CZParametrizationNodeAnalysis(BaseAllCouplersAnalysis):
    single_coupler_analysis_obj = CZParametrizationCouplerAnalysis

    def __init__(self, name, redis_fields, **kwargs):
        super().__init__(name, redis_fields, **kwargs)
