# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024, 2025, 2026
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Amr Osman, 2024
# (C) Chalmers Next Labs 2025, 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from scipy.stats import spearmanr

from tergite_autocalibration.lib.base.analysis import BaseAllCouplersAnalysis
from tergite_autocalibration.lib.nodes.coupler.cz_parametrization.analysis import (
    CZParametrizationAnalysis,
)
from tergite_autocalibration.lib.utils.analysis_models import (
    QuadraticModel,
    SineOscillatingModel,
)
from tergite_autocalibration.utils.dto.qoi import QOI


@dataclass
class ParabolicFit:
    selected_cz_frequencies: np.ndarray
    selected_cz_durations: np.ndarray


class CZChevronCouplerAnalysis(CZParametrizationAnalysis):

    def __init__(self, name, redis_fields, **kwargs):
        super().__init__(name, redis_fields, **kwargs)
        self.model = SineOscillatingModel()
        self.model.set_param_hint("optimal_duration", expr="1/frequency", vary=False)
        self.chevron_model = QuadraticModel()
        self.number_of_working_points: int = kwargs["number_of_working_points"]

    def apply_sinusoidal_slices_fit(self, data):
        # durations is the independent variable in the cosine definition
        guess = self.model.guess(data, x=self.durations)
        try:
            fit = self.model.fit(
                data,
                params=guess,
                x=self.durations,
            )
            duration = fit.values["optimal_duration"]
            amplitude = fit.values["amplitude"]

            fit_data = self.model.eval(fit.params, x=self.fit_plot_durations)

            # discard if the oscillations are not strong enough
            if amplitude < 0.30:
                duration = np.nan
            return np.array([duration]), np.array([fit_data])
        except:
            return np.array([np.nan]), np.array([np.nan])

    def apply_parabolic_fit(
        self, cz_duration_values, cz_working_frequencies
    ) -> ParabolicFit:
        guess_params = self.chevron_model.guess(
            cz_duration_values, x=cz_working_frequencies
        )
        try:
            self.chevron_fit_result = self.chevron_model.fit(
                cz_duration_values, params=guess_params, x=cz_working_frequencies
            )
            # x0 is the frequency at the parabola vertex
            x0 = self.chevron_fit_result.params["x0"].value

            # determine wheteher the residuals are randomly distributed
            # as they should for a good fit
            residuals = cz_duration_values - self.chevron_fit_result.best_fit
            distances_from_vertex = np.abs(cz_working_frequencies - x0)
            correlation = spearmanr(distances_from_vertex, residuals)
            fit_is_good = correlation.statistic < 0.3

            # if the vertex is contained, return a number of
            # frequency duration pairs around it
            vertex_is_contained = (
                cz_working_frequencies.min() < x0 and x0 < cz_working_frequencies.max()
            )
            abs_distances_from_vertex = np.abs(cz_working_frequencies - x0)
            sorted_distances_from_vertex = np.sort(abs_distances_from_vertex)
            num_of_working_pairs = self.number_of_working_points
            distance_threshold = sorted_distances_from_vertex[num_of_working_pairs]
            selected_cz_frequencies = cz_working_frequencies[
                abs_distances_from_vertex < distance_threshold
            ]
            selected_cz_durations = cz_duration_values[
                abs_distances_from_vertex < distance_threshold
            ]
            int_selected_durations_in_ns = (selected_cz_durations // 1e-9).astype(int)
            # ensure durations are in multiples of 4ns:
            selected_cz_durations_in_ns = (int_selected_durations_in_ns // 4) * 4
            parabolic_fit = ParabolicFit(
                selected_cz_frequencies, selected_cz_durations_in_ns
            )
            return parabolic_fit
        except:
            return ParabolicFit(np.nan, np.nan)

    def analyze_coupler(self) -> QOI:
        """Analyze the chevron pattern measured while sweeping the flux duration and frequency.

        Analyze the chevron pattern measured while sweeping the flux pulse duration (y-axis)
        and flux pulse frequency (x-axis).
        The method assigns value to the attributes
         - self.cz_working_durations_in_ns
         - self.cz_working_frequencies
        which correspond to all the (frequency, duration) points where a return to the |11> is observed
        The working pairs may be unnesasrily mainy, sothe method assigns value also to the attributes
         - self.selected_cz_durations_in_ns
         - self.selected_cz_frequencies
        which are a subset of the wotking points with array size according to self.number_of_working_points
        """
        self.calculate_probabilities()

        self.fit_plot_durations = np.linspace(
            self.durations[0], self.durations[-1], 200
        )  # x-values for plotting

        probabilities = self.probabilities
        control_state_2 = probabilities.sel({"qubit": self.control_qubit, "state": 2})
        control_state_1 = probabilities.sel({"qubit": self.control_qubit, "state": 1})
        control_state_0 = probabilities.sel({"qubit": self.control_qubit, "state": 0})
        target_state_0 = probabilities.sel({"qubit": self.target_qubit, "state": 0})
        target_state_1 = probabilities.sel({"qubit": self.target_qubit, "state": 1})
        target_state_2 = probabilities.sel({"qubit": self.target_qubit, "state": 2})

        if self.phase_path == "via_02":
            self.control_diffs = control_state_0 - control_state_1  # - control_state_0
            self.target_diffs = target_state_2 - target_state_1  # - target_state_2
        elif self.phase_path == "via_20":
            self.control_diffs = control_state_2 - control_state_1  # - control_state_2
            self.target_diffs = target_state_0 - target_state_1  # - control_state_0
        else:
            raise ValueError("Invalid phase path")

        self.combined_data = self.control_diffs + self.target_diffs

        # apply a sinusoidal fit to each verical slice (column of specific frequency)
        cz_durations, self.fit_plot_probs = xr.apply_ufunc(
            self.apply_sinusoidal_slices_fit,
            self.combined_data,
            input_core_dims=[[self.durations_coord]],
            output_core_dims=[["cz_pulse_durations"], ["plot_points"]],
            vectorize=True,
        )

        # cleanup entries with nan values from rejected fits:
        cz_durations = cz_durations.dropna(dim=self.frequencies_coord)
        cz_duration_values = cz_durations.values.flatten()

        integer_gate_durations_in_ns = (cz_duration_values // 1e-9).astype(int)
        # ensure durations are in multiples of 4ns:
        cz_working_durations_in_ns = (integer_gate_durations_in_ns // 4) * 4
        cz_working_frequencies = cz_durations.cz_pulse_frequencies.values

        # fit the working points to a parabola model to extract the peak of the chevron
        parabolic_fit = self.apply_parabolic_fit(
            cz_duration_values, cz_working_frequencies
        )
        selected_cz_frequencies = parabolic_fit.selected_cz_frequencies
        selected_cz_durations_in_ns = parabolic_fit.selected_cz_durations

        self.cz_working_frequencies = cz_working_frequencies
        self.cz_working_durations_in_ns = cz_working_durations_in_ns

        self.selected_frequencies = selected_cz_frequencies
        self.selected_durations_in_ns = selected_cz_durations_in_ns

        selected_cz_durations_in_ns = selected_cz_durations_in_ns.tolist()
        selected_cz_frequencies = selected_cz_frequencies.astype(int).tolist()

        selected_frequencies_str = str(selected_cz_frequencies)
        selected_cz_durations_in_ns_str = str(selected_cz_durations_in_ns)
        analysis_succesful = True
        analysis_result = {
            "cz_working_frequencies": {
                "value": selected_frequencies_str,
                "error": 0,
            },
            "cz_working_durations_in_ns": {
                "value": selected_cz_durations_in_ns_str,
                "error": 0,
            },
        }
        qoi = QOI(analysis_result, analysis_succesful)
        return qoi

    @property
    def processed_dataset(self):
        return self.probabilities

    def plotter(self, figures_dictionary):

        current_probabilities = self.probabilities
        current_probabilities.plot(
            x=self.frequencies_coord, cmap="RdBu_r", row="qubit", col="state"
        )

        fig = plt.gcf()
        parabolic_fit_frequencies = np.linspace(
            self.cz_working_frequencies[0], self.cz_working_frequencies[-1], 100
        )
        parabolic_fit_durations = self.chevron_fit_result.eval(
            self.chevron_fit_result.params, x=parabolic_fit_frequencies
        )

        # if there are no working points return only the faceting plot
        if self.cz_working_durations_in_ns.size == 0:
            figures_dictionary[self.coupler] = [fig]
            return

        # for every one of the six faceting axes, plot the working points and
        # their parabolic fit
        for ax in fig.axes:
            ax.plot(
                parabolic_fit_frequencies,
                parabolic_fit_durations,
                color="grey",
                lw=5,
            )
            ax.plot(
                self.cz_working_frequencies,
                self.cz_working_durations_in_ns * 1e-9,
                marker="8",
                ls="",
                color="yellow",
            )
            ax.plot(
                self.selected_frequencies,
                self.selected_durations_in_ns * 1e-9,
                marker="*",
                markersize=12,
                ls="",
                color="yellow",
            )

        figures_dictionary[self.coupler] = [fig]
        plt.show()

    # def plot_frequency_slice(self, freq_index: int):
    #     fig2, ax = plt.subplots()
    #     probs = self.combined_data.isel({self.frequencies_coord: freq_index})
    #     probs.plot.line("bo")
    #     prob_slice = self.fit_plot_probs.isel({self.frequencies_coord: freq_index})
    #     ax.plot(self.fit_plot_durations, prob_slice, "ro-", ms=4)
    #     plt.show()


class CZChevronAnalysis(BaseAllCouplersAnalysis):
    single_coupler_analysis_obj = CZChevronCouplerAnalysis

    def __init__(self, name, redis_fields, **kwargs):
        super().__init__(name, redis_fields, **kwargs)
