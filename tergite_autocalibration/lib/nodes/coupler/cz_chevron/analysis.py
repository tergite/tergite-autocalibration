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

from tergite_autocalibration.lib.base.analysis import BaseAllCouplersAnalysis
from tergite_autocalibration.lib.nodes.coupler.cz_parametrization.analysis import (
    CZParametrizationAnalysis,
)
from tergite_autocalibration.lib.utils.analysis_models import SineOscillatingModel
from tergite_autocalibration.utils.dto.qoi import QOI


class CZChevronCouplerAnalysis(CZParametrizationAnalysis):

    def __init__(self, name, redis_fields, **kwargs):
        super().__init__(name, redis_fields, **kwargs)
        self.model = SineOscillatingModel()
        # # Assume we start from a minimum
        # self.model.set_param_hint("phase", expr="3.141592653589793", vary=True)

        # Pi-pulse amplitude can be derived from the oscillation frequency
        self.model.set_param_hint(
            "optimal_duration",
            expr="1/frequency",
            vary=False,
            # "optimal_duration", expr="1/frequency - phase/(2*pi*frequency)", vary=False
        )

    def apply_cz_fit(self, data):
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
            if amplitude < 0.55:
                duration = np.nan
            return np.array([duration]), np.array([fit_data])
        except:
            return np.array([np.nan]), np.array([np.nan])
            print("error")

    def analyze_coupler(self):
        self.calculate_probabilities()

        self.fit_plot_durations = np.linspace(
            self.durations[0], self.durations[-1], 200
        )  # x-values for plotting
        self.optimal_values = {}

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

        print(f"{ self.phase_path = }")
        cz_optimal_durations, self.fit_plot_probs = xr.apply_ufunc(
            self.apply_cz_fit,
            self.combined_data,
            input_core_dims=[[self.durations_coord]],
            output_core_dims=[["cz_pulse_durations"], ["plot_points"]],
            vectorize=True,
        )

        # drop bad fits
        # cz_optimal_durations = cz_optimal_durations.where(cz_optimal_durations < 500e-9)

        # cleanup entries with nan values from rejected fits:
        self.cz_optimal_durations = cz_optimal_durations.dropna(
            dim=self.frequencies_coord
        )

        integer_gate_durations_in_ns = (
            (self.cz_optimal_durations // 1e-9).astype(int).values.flatten()
        )
        # ensure durations are in multiples of 4ns:
        cz_working_durations_in_ns = (integer_gate_durations_in_ns // 4) * 4
        cz_working_durations_in_ns = cz_working_durations_in_ns.tolist()
        cz_working_frequencies = self.cz_optimal_durations.cz_pulse_frequencies
        cz_working_frequencies = cz_working_frequencies.astype(int).values.tolist()

        cz_working_frequencies_str = str(cz_working_frequencies)
        cz_working_durations_in_ns_str = str(cz_working_durations_in_ns)

        # self.plot_frequency_slice(4)
        # self.plot_frequency_slice(6)
        # self.plot_frequency_slice(8)

        analysis_succesful = True
        analysis_result = {
            "cz_working_frequencies": {
                "value": cz_working_frequencies_str,
                "error": 0,
            },
            "cz_working_durations_in_ns": {
                "value": cz_working_durations_in_ns_str,
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
            x=self.frequencies_coord,
            cmap="RdBu_r",
            row="qubit",
            col="state",
        )

        fig = plt.gcf()

        if not self.cz_optimal_durations.size == 0:
            for ax in fig.axes:
                self.cz_optimal_durations.plot(
                    # self.cz_optimal_durations.drop_vars("qubit").plot(
                    ax=ax,
                    marker="8",
                    ls="",
                    color="yellow",
                )

        figures_dictionary[self.coupler] = [fig]

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
