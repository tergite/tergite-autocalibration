# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Module containing a class that fits data from a resonator spectroscopy experiment.
"""
import numpy as np
import xarray as xr
from quantify_core.analysis import fitting_models as fm

from tergite_autocalibration.config.settings import REDIS_CONNECTION
from tergite_autocalibration.lib.base.analysis import (
    BaseAllQubitsAnalysis,
    BaseQubitAnalysis,
)

model = fm.ResonatorModel()


class ResonatorSpectroscopyQubitAnalysis(BaseQubitAnalysis):
    """
    Analysis that fits the data of a resonator spectroscopy experiment for one qubit.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.fit_results = {}

    def analyse_qubit(self):
        coord_name = list(self.coord.keys())[0]
        frequencies = self.dataset.coords[coord_name].values

        if isinstance(self.S21, xr.Dataset):
            data_var_name = list(self.S21.data_vars.keys())[
                0
            ]  # Adjust if specific variable name is known
            s21_dataarray = self.S21[data_var_name]
        else:
            raise TypeError("Expected self.S21 to be an xarray.DataArray")
        s21_values = s21_dataarray.values

        # Gives an initial guess for the model parameters and then fits the model to the data.
        guess = model.guess(s21_values, f=frequencies)
        self.fitting_model = model.fit(s21_values, params=guess, f=frequencies)

        fit_result = self.fitting_model

        fit_fr = fit_result.params["fr"].value
        self.uncertainty = fit_result.params["fr"].stderr

        fit_Ql = fit_result.params["Ql"].value
        fit_Qe = fit_result.params["Qe"].value
        fit_ph = fit_result.params["theta"].value

        # analytical expression, probably an interpolation of the fit would be better
        self.minimum_freq = (
            fit_fr
            / (4 * fit_Qe * fit_Ql * np.sin(fit_ph))
            * (
                4 * fit_Qe * fit_Ql * np.sin(fit_ph)
                - 2 * fit_Qe * np.cos(fit_ph)
                + fit_Ql
                + np.sqrt(
                    4 * fit_Qe**2 - 4 * fit_Qe * fit_Ql * np.cos(fit_ph) + fit_Ql**2
                )
            )
        )
        # using the min value driectly
        self.min_freq_data = frequencies[np.argmin(np.abs(s21_values))]
        # print(fit_Ql)
        # print(self.min_freq )
        return [self.minimum_freq, fit_Ql, self.min_freq_data]

    def plotter(self, ax):
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("|S21| (V)")
        self.fitting_model.plot_fit(ax, numpoints=400, xlabel=None, title=None)
        ax.axvline(
            self.minimum_freq,
            c="blue",
            ls="solid",
            label=f"f = {self.minimum_freq:.6E} ± {self.uncertainty:.1E} (Hz)",
        )
        ax.grid()


class ResonatorSpectroscopy1QubitAnalysis(ResonatorSpectroscopyQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.fit_results = {}

    def plotter(self, ax):
        # breakpoint()
        this_qubit = self.dataset.attrs["qubit"]
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("|S21| (V)")
        ro_freq = float(
            REDIS_CONNECTION.hget(f"transmons:{this_qubit}", "clock_freqs:readout")
        )
        self.fitting_model.plot_fit(ax, numpoints=400, xlabel=None, title=None)
        ax.axvline(self.minimum_freq, c="green", ls="solid", label="frequency |1> ")
        ax.axvline(ro_freq, c="blue", ls="dashed", label="frequency |0>")
        ax.grid()


class ResonatorSpectroscopy2QubitAnalysis(ResonatorSpectroscopyQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.fit_results = {}

    def plotter(self, ax):
        this_qubit = self.dataset.attrs["qubit"]
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("|S21| (V)")
        ro_freq = float(
            REDIS_CONNECTION.hget(f"transmons:{this_qubit}", "clock_freqs:readout")
        )
        ro_freq_1 = float(
            REDIS_CONNECTION.hget(
                f"transmons:{this_qubit}", "extended_clock_freqs:readout_1"
            )
        )
        self.fitting_model.plot_fit(ax, numpoints=400, xlabel=None, title=None)
        ax.axvline(self.minimum_freq, c="red", ls="solid", label="frequency |2>")
        ax.axvline(ro_freq_1, c="green", ls="dashed", label="frequency |1>")
        ax.axvline(ro_freq, c="blue", ls="dashed", label="frequency |0>")
        ax.grid()


class ResonatorSpectroscopyNodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = ResonatorSpectroscopyQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)


class ResonatorSpectroscopy1NodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = ResonatorSpectroscopy1QubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)


class ResonatorSpectroscopy2NodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = ResonatorSpectroscopy2QubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
