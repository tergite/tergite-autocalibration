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

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.lib.base.analysis import (
    BaseAllCouplersAnalysis,
    BaseCouplerAnalysis,
)
from tergite_autocalibration.lib.utils.analysis_models import (
    RamseyModel,
    straighten_ramsey_points,
)
from tergite_autocalibration.utils.dto.qoi import QOI


class ZZCouplingCouplerAnalysis(BaseCouplerAnalysis):
    model = RamseyModel()

    def __init__(self, name, redis_fields, **kwargs):
        super().__init__(name, redis_fields)
        self.active_qubit = kwargs["active_qubit"]
        self.spectator_qubit = kwargs["spectator_qubit"]

    def apply_ramsey_fit(self, data):
        guess = self.model.guess(data, t=self.active_ramsey_delays)
        fit = self.model.fit(data, params=guess, t=self.active_ramsey_delays)
        fitted_detuning = fit.params["frequency"].value
        return np.array([fitted_detuning])

    def _analyse_ramsey(self):
        active_qubit = self.active_qubit
        spectator_qubit = self.spectator_qubit
        ds_coords = self.dataset.coords
        for coord in self.dataset.coords:
            coord = str(coord)
            if "delay" in coord:
                if active_qubit in coord:
                    self.active_delay_coord = coord
                    self.active_ramsey_delays = ds_coords[coord].values
                elif spectator_qubit in coord:
                    self.spectator_delay_coord = coord
                    self.spectator_ramsey_delays = ds_coords[coord].values
            elif "detuning" in coord:
                if active_qubit in coord:
                    self.active_detuning_coord = coord
                    self.active_artificial_detunings = ds_coords[coord].values
                if spectator_qubit in coord:
                    self.spectator_detuning_coord = coord
                    self.spectator_artificial_detunings = ds_coords[coord].values
            elif "states" in coord:
                self.spectator_states_coord = coord

        redis_key = f"transmons:{self.active_qubit}"
        redis_value = REDIS_CONNECTION.hget(f"{redis_key}", "clock_freqs:f01")
        active_qubit_frequency = float(redis_value)

        if self.active_qubit == self.control_qubit:
            self.active_data_var = np.abs(self.control_qubit_data_var)
        elif self.active_qubit == self.target_qubit:
            self.active_data_var = np.abs(self.target_qubit_data_var)

        fitted_detunings = xr.apply_ufunc(
            self.apply_ramsey_fit,
            self.active_data_var,
            input_core_dims=[[self.active_delay_coord]],
            # the output is a scalar so we pass an empty array to avoid unnessecary out dimensions:
            output_core_dims=[[]],
            vectorize=True,
        )

        active_fitted_detunings_spec_0 = fitted_detunings.sel(
            {self.spectator_states_coord: 0}
        )
        active_fitted_detunings_spec_1 = fitted_detunings.sel(
            {self.spectator_states_coord: 1}
        )
        self.fitted_detunings_spec_0 = straighten_ramsey_points(
            self.active_artificial_detunings, active_fitted_detunings_spec_0
        )
        self.fitted_detunings_spec_1 = straighten_ramsey_points(
            self.active_artificial_detunings, active_fitted_detunings_spec_1
        )

        m, b = np.polyfit(
            self.active_artificial_detunings, self.fitted_detunings_spec_0, 1
        )
        self.poly1d_fn_spec_0 = np.poly1d((m, b))
        self.frequency_correction_spec_0 = -b / m
        self.corrected_qubit_frequency_spec_0 = (
            active_qubit_frequency + self.frequency_correction_spec_0
        )
        m, b = np.polyfit(
            self.active_artificial_detunings, self.fitted_detunings_spec_1, 1
        )
        self.poly1d_fn_spec_1 = np.poly1d((m, b))
        self.frequency_correction_spec_1 = -b / m
        self.corrected_qubit_frequency_spec_1 = (
            active_qubit_frequency + self.frequency_correction_spec_1
        )

        self.zz_coupling = (
            self.corrected_qubit_frequency_spec_1
            - self.corrected_qubit_frequency_spec_0
        )

    def analyze_coupler(self):
        self._analyse_ramsey()

        analysis_successful = True
        analysis_result = {"zz_coupling": {"value": self.zz_coupling, "error": 0}}

        qoi = QOI(analysis_result, analysis_successful)

        return qoi

    def plotter(self, figures_dictionary):
        fig, axs = plt.subplots(ncols=2)
        axs[0].plot(
            self.active_artificial_detunings, self.fitted_detunings_spec_0, "bo", ms=5.0
        )
        axs[0].axvline(
            self.frequency_correction_spec_0,
            color="red",
            label=rf"{self.active_qubit} f01: {int(self.corrected_qubit_frequency_spec_0) / 1e6:.4f} MHz",
        )
        axs[0].plot(
            self.active_artificial_detunings,
            self.poly1d_fn_spec_0(self.active_artificial_detunings),
            "--b",
            lw=1,
        )
        axs[0].axvline(0, color="black", lw=1)
        axs[0].set_xlabel("Artificial detuning (Hz)")
        axs[0].set_ylabel("Fitted detuning (Hz)")

        axs[0].set_title(rf"spectator {self.spectator_qubit} at $|0\rangle$")
        axs[0].grid()
        axs[0].legend()

        axs[1].plot(
            self.active_artificial_detunings, self.fitted_detunings_spec_1, "bo", ms=5.0
        )
        axs[1].axvline(
            self.frequency_correction_spec_1,
            color="red",
            label=rf"{self.active_qubit} f01: {int(self.corrected_qubit_frequency_spec_1) / 1e6:.4f} MHz",
        )
        axs[1].plot(
            self.active_artificial_detunings,
            self.poly1d_fn_spec_1(self.active_artificial_detunings),
            "--b",
            lw=1,
        )
        axs[1].axvline(0, color="black", lw=1)
        axs[1].set_xlabel("Artificial detuning (Hz)")
        axs[1].set_ylabel("Fitted detuning (Hz)")

        axs[1].set_title(rf"spectator {self.spectator_qubit} at $|1\rangle$")
        axs[1].grid()
        axs[1].legend()

        figures_dictionary[self.coupler] = [fig]


class ZZCouplingNodeAnalysis(BaseAllCouplersAnalysis):
    single_coupler_analysis_obj = ZZCouplingCouplerAnalysis

    def __init__(self, name, redis_fields, **kwargs):
        super().__init__(name, redis_fields, **kwargs)
