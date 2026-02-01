# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024, 2025, 2026
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Amr Osman 2024
# (C) Copyright Chalmers Next Labs AB 2024, 2025, 2026
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

from tergite_autocalibration.lib.base.analysis import (BaseAllCouplersAnalysis,
                                                       BaseCouplerAnalysis)
from tergite_autocalibration.lib.utils.analysis_models import \
    SineOscillatingModel
from tergite_autocalibration.lib.utils.classification_functions import \
    calculate_probabilities
from tergite_autocalibration.utils.dto.qoi import QOI


class CZCalibrationCouplerAnalysis(BaseCouplerAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.model = SineOscillatingModel()
        self.model.set_param_hint("phase", min=-360, max=360, vary=True)

    def apply_cz_fit(self, data):
        guess = self.model.guess(data, x=self.target_phases)
        fit = self.model.fit(
            data,
            params=guess,
            x=self.target_phases,
        )
        phase = fit.values["phase"]
        fit_data = self.model.eval(fit.params, x=self.fit_plot_phases)
        return np.array([phase]), np.array([fit_data])

    def analyze_coupler(self):

        for coord in self.S21.coords:
            coord = str(coord)
            if "control_ons" in coord:
                self.control_mode_coord = coord
            elif "dc_currents" in coord:
                self.dc_currents_coord = coord
                self.dc_currents = self.S21[self.dc_currents_coord].values
            elif "cz_frequencies" in coord:
                self.cz_frequencies_coord = coord
                self.cz_frequencies = self.S21[coord].values
                self.number_of_frequencies = self.S21[coord].size
            elif "working_points" in coord:
                self.cz_working_points_coord = coord
                self.cz_working_points = self.S21[coord].values
                self.number_of_wp = self.S21[coord].size
                self.frequencies, self.durations = zip(*self.cz_working_points)
            elif "ramsey_phases" in coord:
                if self.control_qubit in coord:
                    self.control_phase_coord = coord
                elif self.target_qubit in coord:
                    self.target_phase_coord = coord
                    self.target_phases = self.S21[coord].values
            elif "loops" in coord:
                self.loops_coord = coord
                self.number_of_loops = self.S21[self.loops_coord].size

        self.control_qubit_probabilities = calculate_probabilities(
            self.control_qubit_data_var
        )
        self.target_qubit_probabilities = calculate_probabilities(
            self.target_qubit_data_var
        )

        self.fit_plot_phases = np.linspace(
            self.target_phases[0], self.target_phases[-1], 200
        )  # x-values for plotting

        data_target_0 = self.target_qubit_probabilities.sel({"state": 0})

        self.delta_phi_0, target_plot_points_0 = xr.apply_ufunc(
            self.apply_cz_fit,
            data_target_0,
            input_core_dims=[[self.target_phase_coord]],
            output_core_dims=[["phases"], ["plot_points"]],
            vectorize=True,
        )
        self.target_plot_points_0 = target_plot_points_0.assign_coords(
            {"plot_points": self.fit_plot_phases}
        )
        self.target_plot_points_0 = self.target_plot_points_0.rename(
            {"plot_points": self.target_phase_coord}
        )

        phi_on = self.delta_phi_0.sel({self.control_mode_coord: True})
        phi_off = self.delta_phi_0.sel({self.control_mode_coord: False})
        deltas = abs((np.rad2deg(phi_on - phi_off) + 360) % 360 - 180)
        self.optimal_point_index = deltas.argmin().item()
        optimal_frequency = self.frequencies[self.optimal_point_index]
        optimal_duration = self.durations[self.optimal_point_index]

        analysis_succesful = True
        analysis_result = {
            "cz_pulse_frequency": {
                "value": optimal_frequency,
                "error": 0,
            },
            "cz_pulse_duration": {
                "value": optimal_duration,
                "error": 0,
            },
        }
        qoi = QOI(analysis_result, analysis_succesful)
        return qoi

    @property
    def processed_dataset(self):
        return self.target_qubit_probabilities

    def plotter(self, figures_dictionary):

        figures_list = []
        number_of_plots = self.number_of_wp + 1
        ncols = 5
        n_rows = max(1, int(np.ceil(number_of_plots / ncols)))

        fig, axs = plt.subplots(
            ncols=ncols,
            nrows=n_rows,
            sharex=True,
            sharey=True,
            squeeze=False,
        )
        # leak_fig, leak_axs = plt.subplots(
        #     ncols=ncols,
        #     nrows=n_rows,
        #     sharex=True,
        #     sharey=True,
        #     # squeeze=False,
        # )

        for i, _ in enumerate(self.cz_working_points):
            title_color = "black"
            if i == self.optimal_point_index:
                title_color = "red"

            col = i % ncols
            row = i // ncols
            phi_on = self.delta_phi_0.sel({self.control_mode_coord: True}).isel(
                {self.cz_working_points_coord: i}
            )
            phi_off = self.delta_phi_0.sel({self.control_mode_coord: False}).isel(
                {self.cz_working_points_coord: i}
            )
            delta_phi = np.rad2deg((phi_off - phi_on).values[0])

            target_probabilities = self.target_qubit_probabilities.isel(
                {self.cz_working_points_coord: i}
            )
            control_probabilities = self.control_qubit_probabilities.isel(
                {self.cz_working_points_coord: i}
            )

            self.target_plot_points_0.isel({self.cz_working_points_coord: i}).sel(
                {self.control_mode_coord: True}
            ).plot(
                ax=axs[row][col],
                x=self.target_phase_coord,
                color="orange",
            )
            self.target_plot_points_0.isel({self.cz_working_points_coord: i}).sel(
                {self.control_mode_coord: False}
            ).plot(
                ax=axs[row][col],
                x=self.target_phase_coord,
                color="black",
            )

            target_probabilities.sel({"state": 0, self.control_mode_coord: True}).plot(
                ax=axs[row][col],
                x=self.target_phase_coord,
                marker="o",
                color="orange",
                ls="",
            )
            target_probabilities.sel({"state": 0, self.control_mode_coord: False}).plot(
                ax=axs[row][col],
                x=self.target_phase_coord,
                marker="o",
                color="black",
                ls="",
                label=f"Phase: {delta_phi:.1f} $^o$",
            )
            target_probabilities.sel({"state": 1, self.control_mode_coord: True}).plot(
                ax=axs[row][col],
                x=self.target_phase_coord,
                marker="o",
                color="tomato",
                ls="",
            )
            target_probabilities.sel({"state": 1, self.control_mode_coord: False}).plot(
                ax=axs[row][col],
                x=self.target_phase_coord,
                marker="o",
                color="grey",
                ls="",
            )
            # target_probabilities.sel({"state": 2, self.control_mode_coord: True}).plot(
            #     ax=leak_axs[row][col],
            #     x=self.target_phase_coord,
            #     marker="o",
            #     color="green",
            #     ls="",
            # )
            # target_probabilities.sel({"state": 2, self.control_mode_coord: False}).plot(
            #     ax=leak_axs[row][col],
            #     x=self.target_phase_coord,
            #     marker="o",
            #     color="olivedrab",
            #     ls="",
            # )
            # control_probabilities.sel({"state": 2, self.control_mode_coord: True}).plot(
            #     ax=leak_axs[row][col],
            #     x=self.control_phase_coord,
            #     marker="x",
            #     color="pink",
            #     ls="",
            # )
            # control_probabilities.sel(
            #     {"state": 2, self.control_mode_coord: False}
            # ).plot(
            #     ax=leak_axs[row][col],
            #     x=self.control_phase_coord,
            #     marker="x",
            #     color="purple",
            #     ls="",
            # )
            axs[row][col].set_title(
                f"freq: {self.frequencies[i]:.4e} duration: {self.durations[i]:.3e}",
                color=title_color,
                fontsize=10,
            )
            axs[row][col].legend()

        phis_on = self.delta_phi_0.sel({self.control_mode_coord: True})
        phis_off = self.delta_phi_0.sel({self.control_mode_coord: False})
        delta_phis = np.rad2deg((phis_off - phis_on).values)
        print(f"{ self.frequencies = }")
        print(f"{ delta_phis.flatten() = }")
        arc_fig, ax = plt.subplots()
        ax.plot(self.frequencies, delta_phis, "bo")

        fig.suptitle("State 0: On orange Off black")
        figures_list.append(fig)
        # figures_list.append(leak_fig)
        figures_list.append(arc_fig)
        figures_dictionary[self.coupler] = figures_list


class CZCalibrationNodeAnalysis(BaseAllCouplersAnalysis):
    single_coupler_analysis_obj = CZCalibrationCouplerAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)



