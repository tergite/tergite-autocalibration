# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024, 2025, 2026
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Amr Osman 2024
# (C) Copyright Chalmers Next Labs 2024, 2025, 2026
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
from cycler import cycler

from tergite_autocalibration.lib.base.analysis import (
    BaseAllCouplersAnalysis,
    BaseCouplerAnalysis,
)
from tergite_autocalibration.lib.utils.analysis_models import SineOscillatingModel
from tergite_autocalibration.lib.utils.classification_functions import (
    calculate_probabilities,
)
from tergite_autocalibration.utils.dto.qoi import QOI


class CZDynamicPhaseCouplerAnalysis(BaseCouplerAnalysis):

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.model = SineOscillatingModel()

    def sinusoidal_fit(self, data):
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
        dataset = self.S21
        for coord in dataset.coords:
            coord = str(coord)
            if "loops" in coord:
                self.loops_coord = coord
                self.number_of_loops = dataset[coord].size
            elif "phases" in coord:
                if dataset[coord].attrs["qubit"] == self.control_qubit:
                    self.control_phases_coord = coord
                    self.control_phases = self.S21[coord].values
                elif dataset[coord].attrs["qubit"] == self.target_qubit:
                    self.target_phases_coord = coord
                    self.target_phases = self.S21[coord].values
            elif "swap" in coord:
                self.swap_coord = coord
                self.swap_modes = dataset[coord].values
            elif "gate" in coord:
                self.gate_mode_coord = coord
                self.gate_modes = dataset[coord].values
            else:
                raise ValueError

        self.control_qubit_probabilities = calculate_probabilities(
            self.control_qubit_data_var
        )
        self.target_qubit_probabilities = calculate_probabilities(
            self.target_qubit_data_var
        )

        self.fit_plot_phases = np.linspace(
            self.target_phases[0], self.target_phases[-1], 400
        )  # x-values for plotting

        # apply sinusoidal fit on the state |1> of the target qubit and...
        data_target_1 = self.target_qubit_probabilities.sel(
            {"state": 1, self.swap_coord: False}
        )
        # ... the state |1> of the control qubit while we have swaped.
        data_control_swap_1 = self.control_qubit_probabilities.sel(
            {"state": 1, self.swap_coord: True}
        )

        phi_fits, target_plot_points_1 = xr.apply_ufunc(
            self.sinusoidal_fit,
            data_target_1,
            input_core_dims=[[self.target_phases_coord]],
            output_core_dims=[["phases"], ["plot_points"]],
            vectorize=True,
        )
        phi_swaped_fits, control_swap_plot_points_1 = xr.apply_ufunc(
            self.sinusoidal_fit,
            data_control_swap_1,
            input_core_dims=[[self.control_phases_coord]],
            output_core_dims=[["phases"], ["plot_points"]],
            vectorize=True,
        )
        self.target_plot_points = target_plot_points_1.assign_coords(
            {"plot_points": self.fit_plot_phases}
        )
        self.target_plot_points = self.target_plot_points.rename(
            {"plot_points": self.target_phases_coord}
        )
        self.control_swaped_plot_points = control_swap_plot_points_1.assign_coords(
            {"plot_points": self.fit_plot_phases}
        )
        self.control_swaped_plot_points = self.control_swaped_plot_points.rename(
            {"plot_points": self.control_phases_coord}
        )

        # phase 01 correction
        phi_gate_on = phi_fits.sel({self.gate_mode_coord: True})
        phi_gate_off = phi_fits.sel({self.gate_mode_coord: False})
        phi_01_rad = (phi_gate_on - phi_gate_off).item()
        self.phase_01 = np.rad2deg(phi_01_rad)

        # phase 10 correction
        phi_swaped_gate_on = phi_swaped_fits.sel({self.gate_mode_coord: True})
        phi_swaped_gate_off = phi_swaped_fits.sel({self.gate_mode_coord: False})
        phi_10_rad = (phi_swaped_gate_on - phi_swaped_gate_off).item()
        self.phase_10 = np.rad2deg(phi_10_rad)

        analysis_succesful = True
        analysis_result = {
            "control_local_phase": {
                "value": self.phase_10,
                "error": 0,
            },
            "target_local_phase": {
                "value": self.phase_01,
                "error": 0,
            },
        }
        qoi = QOI(analysis_result, analysis_succesful)
        return qoi

    @property
    def processed_dataset(self):
        self.probabilities = xr.concat(
            [self.control_qubit_probabilities, self.target_qubit_probabilities],
            dim="qubit",
        )
        return self.probabilities

    def plotter(self, figures_dictionary):
        fig, axs = plt.subplots(ncols=2, nrows=2, sharey=True, sharex=True)
        target_probabilities = self.target_qubit_probabilities.sel({"state": 1})
        control_probabilities = self.control_qubit_probabilities.sel({"state": 1})

        styles = {"marker": "o", "ls": ""}
        text_styles = {
            "size": 16,
            "color": "red",
            "backgroundcolor": "white",
        }

        #  normal qubits (not swaped) for phi_10
        swap = False
        axs[0][0].set_prop_cycle(cycler("color", ["orange", "black"]))
        control_probabilities.sel({self.swap_coord: swap}).plot(
            ax=axs[0][0], hue=self.gate_mode_coord, **styles
        )
        axs[0][0].set_title(f"swap: {swap}")

        axs[0][1].set_prop_cycle(cycler("color", ["orange", "black"]))
        target_probabilities.sel({self.swap_coord: swap}).plot(
            ax=axs[0][1],
            hue=self.gate_mode_coord,
            **styles,
        )
        axs[0][1].text(
            0,
            0,
            f"$\\varphi_{{01}} = {self.phase_01:.1f} ^o$",
            bbox=dict(facecolor="white", alpha=0.5, linewidth=0),
            **text_styles,
        )
        axs[0][1].get_legend().remove()
        # plot sinusoidal fits:
        self.target_plot_points.plot(ax=axs[0][1], hue=self.gate_mode_coord)
        axs[0][1].set_title(f"swap: {swap}")

        # swaped qubits for phi_01
        swap = True
        axs[1][0].set_prop_cycle(cycler("color", ["orange", "black"]))
        control_probabilities.sel({self.swap_coord: swap}).plot(
            ax=axs[1][0],
            hue=self.gate_mode_coord,
            **styles,
        )
        # plot sinusoidal fits:
        self.control_swaped_plot_points.plot(ax=axs[1][0], hue=self.gate_mode_coord)
        axs[1][0].text(
            0,
            0,
            f"$\\varphi_{{10}} = {self.phase_10:.1f} ^o$",
            bbox=dict(facecolor="white", alpha=0.5, linewidth=0),
            **text_styles,
        )
        axs[1][0].get_legend().remove()
        axs[1][0].set_title(f"swap: {swap}")

        axs[1][1].set_prop_cycle(cycler("color", ["orange", "black"]))
        target_probabilities.sel({self.swap_coord: True}).plot(
            ax=axs[1][1], hue=self.gate_mode_coord, **styles
        )
        axs[1][1].set_title(f"swap: {swap}")

        figures_dictionary[self.coupler] = [fig]


class CZ_LocalPhasesNodeAnalysis(BaseAllCouplersAnalysis):
    single_coupler_analysis_obj = CZDynamicPhaseCouplerAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
