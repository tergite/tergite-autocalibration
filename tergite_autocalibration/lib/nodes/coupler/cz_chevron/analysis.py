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


class CZChevronCouplerAnalysis(CZParametrizationAnalysis):

    def __init__(self, name, redis_fields, **kwargs):
        super().__init__(name, redis_fields, **kwargs)
        self.model = SineOscillatingModel()
        self.model.set_param_hint("optimal_duration", expr="1/frequency", vary=False)
        self.chevron_model = QuadraticModel()

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
            print(f"{ amplitude = }")

            fit_data = self.model.eval(fit.params, x=self.fit_plot_durations)

            # discard if the oscillations are not strong enough
            if amplitude < 0.30:
                duration = np.nan
            return np.array([duration]), np.array([fit_data])
        except:
            return np.array([np.nan]), np.array([np.nan])

    def analyze_coupler(self):
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

        cz_durations, self.fit_plot_probs = xr.apply_ufunc(
            self.apply_sinusoidal_slices_fit,
            self.combined_data,
            input_core_dims=[[self.durations_coord]],
            output_core_dims=[["cz_pulse_durations"], ["plot_points"]],
            vectorize=True,
        )

        # drop bad fits
        # cz_optimal_durations = cz_optimal_durations.where(cz_optimal_durations < 500e-9)

        # cleanup entries with nan values from rejected fits:
        cz_durations = cz_durations.dropna(dim=self.frequencies_coord)

        integer_gate_durations_in_ns = (
            (cz_durations // 1e-9).astype(int).values.flatten()
        )
        # ensure durations are in multiples of 4ns:
        cz_working_durations_in_ns = (integer_gate_durations_in_ns // 4) * 4
        cz_working_frequencies = cz_durations.cz_pulse_frequencies.values

        # fit the working points to a parabola model to extract the peak of the chevron
        cz_duration_values = cz_durations.values.flatten()
        guess_params = self.chevron_model.guess(
            cz_duration_values, x=cz_working_frequencies
        )

        self.cz_working_durations = cz_duration_values
        self.cz_working_frequencies = cz_working_frequencies

        self.chevron_fit_result = self.chevron_model.fit(
            cz_duration_values, params=guess_params, x=cz_working_frequencies
        )
        print(self.chevron_fit_result.fit_report())
        residuals = cz_duration_values - self.chevron_fit_result.best_fit
        x0 = self.chevron_fit_result.params["x0"].value
        distances_from_vertex = np.abs(cz_working_frequencies - x0)

        correlation = spearmanr(distances_from_vertex, residuals)

        fit_is_good = correlation.statistic < 0.3
        vertex_is_contained = (
            cz_working_frequencies.min() < x0 and x0 < cz_working_frequencies.max()
        )
        print(f"{ fit_is_good = }")
        print(f"{ vertex_is_contained = }")
        abs_distances_from_vertex = np.abs(cz_working_frequencies - x0)
        sorted_distances_from_vertex = np.sort(abs_distances_from_vertex)
        num_of_working_pairs = 7
        distance_threshold = sorted_distances_from_vertex[num_of_working_pairs]
        selected_cz_frequencies = cz_working_frequencies[
            abs_distances_from_vertex < distance_threshold
        ]

        selected_cz_duartions_in_ns = cz_working_durations_in_ns[
            abs_distances_from_vertex < distance_threshold
        ]

        self.selected_frequencies = selected_cz_frequencies
        self.selected_durations = selected_cz_duartions_in_ns * 1e-9

        selected_cz_duartions_in_ns = selected_cz_duartions_in_ns.tolist()
        selected_cz_frequencies = selected_cz_frequencies.astype(int).tolist()

        selected_frequencies_str = str(selected_cz_frequencies)
        selected_cz_durations_in_ns_str = str(selected_cz_duartions_in_ns)
        print(f"{ selected_cz_duartions_in_ns = }")
        print(f"{ selected_cz_frequencies = }")
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
        fit_kws = {"c": "black"}

        if not self.cz_working_durations.size == 0:
            for ax in fig.axes:
                breakpoint()
                self.chevron_fit_result.plot_fit(
                    ax=ax,
                    numpoints=100,
                    fit_kws=fit_kws,
                    title=ax.get_title(),
                    xlabel=None,
                    ylabel=None,
                )
                # ax.get_legend().remove()
                ax.plot(
                    self.cz_working_frequencies,
                    self.cz_working_durations,
                    marker="8",
                    ls="",
                    color="yellow",
                )
                ax.plot(
                    self.selected_frequencies,
                    self.selected_durations,
                    marker="*",
                    markersize=12,
                    ls="",
                    color="green",
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


# # print(f"x0 = {x0:.3f} ± {x0_err:.3f}")
#
#
# resid = ydata - result.best_fit
# axs[2].scatter(xdata, resid, s=20)
# axs[2].axhline(0, color='k')
# axs[2].set_xlabel("x")
# axs[2].set_ylabel("residual")
# axs[2].set_title("Residuals vs x")
# plt.show()
#
# x = xdata
# from scipy.stats import spearmanr
#
# x0 = result.params['x0'].value
# d = np.abs(x - x0)
#
# rho, pval = spearmanr(d, resid)
#
# print(f"Spearman(|x-x0|, resid): rho={rho:.3f}, p={pval:.3g}")
#
# plt.show()
