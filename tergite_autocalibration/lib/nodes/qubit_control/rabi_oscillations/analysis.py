# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Amr Osman 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Module containing classes that model, fit and plot data from a Rabi experiment.
"""
import lmfit
import numpy as np
import xarray as xr
from quantify_core.analysis.fitting_models import fft_freq_phase_guess

from tergite_autocalibration.utils.redis_utils import fetch_redis_params
from ....base.analysis import BaseAnalysis


# Cosine function that is fit to Rabi oscillations
def cos_func(
    drive_amp: float,
    frequency: float,
    amplitude: float,
    offset: float,
    phase: float,
) -> float:
    return amplitude * np.cos(2 * np.pi * frequency * drive_amp + phase) + offset


class RabiModel(lmfit.model.Model):
    """
    Generate a cosine model that can be fit to Rabi oscillation data.
    """

    def __init__(self, *args, **kwargs):
        # Pass in the defining equation so the user doesn't have to later.
        super().__init__(cos_func, *args, **kwargs)

        # Enforce oscillation frequency is positive
        self.set_param_hint("frequency", min=0)

        # Fix the phase at pi so that the ouput is at a minimum when drive_amp=0
        self.set_param_hint("phase", expr="3.141592653589793", vary=True)

        # Pi-pulse amplitude can be derived from the oscillation frequency
        self.set_param_hint("amp180", expr="1/(2*frequency)", vary=False)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        drive_amp = kws.get("drive_amp", None)
        if drive_amp is None:
            return None

        amp_guess = abs(max(data) - min(data)) / 2  # amp is positive by convention
        offs_guess = np.mean(data)

        # Frequency guess is obtained using a fast fourier transform (FFT).
        (freq_guess, _) = fft_freq_phase_guess(data, drive_amp)

        self.set_param_hint("frequency", value=freq_guess, min=0)
        self.set_param_hint("amplitude", value=amp_guess, min=0)
        self.set_param_hint("offset", value=offs_guess)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)


class RabiAnalysis(BaseAnalysis):
    """
    Analysis that fits a cosine function to Rabi oscillation data.
    """

    def __init__(self, dataset: xr.Dataset):
        super().__init__()
        data_var = list(dataset.data_vars.keys())[0]
        coord = list(dataset[data_var].coords.keys())[0]
        self.S21 = dataset[data_var].values
        self.independents = dataset[coord].values
        self.fit_results = {}
        self.qubit = dataset[data_var].attrs["qubit"]

    def analyse_qubit(self):
        # Initialize the Rabi model
        model = RabiModel()

        # Fetch the resulting measurement variables from self
        self.magnitudes = np.absolute(self.S21)
        amplitudes = self.independents

        self.fit_amplitudes = np.linspace(
            amplitudes[0], amplitudes[-1], 400
        )  # x-values for plotting

        # Gives an initial guess for the model parameters and then fits the model to the data.
        guess = model.guess(self.magnitudes, drive_amp=amplitudes)
        fit_result = model.fit(self.magnitudes, params=guess, drive_amp=amplitudes)

        self.ampl = fit_result.params["amp180"].value
        self.uncertainty = fit_result.params["amp180"].stderr

        self.fit_y = model.eval(
            fit_result.params, **{model.independent_vars[0]: self.fit_amplitudes}
        )
        return [self.ampl]

    def plotter(self, ax):
        # Plots the data and the fitted model of a Rabi experiment
        ax.plot(
            self.fit_amplitudes,
            self.fit_y,
            "r-",
            lw=3.0,
            label=f" π_ampl = {self.ampl:.2E} (V)",
        )
        ax.plot(self.independents, self.magnitudes, "bo-", ms=3.0)
        ax.set_title(f"Rabi Oscillations for {self.qubit}")
        ax.set_xlabel("Amplitude (V)")
        ax.set_ylabel("|S21| (V)")
        ax.grid()


class NRabiAnalysis(BaseAnalysis):
    def __init__(self, dataset: xr.Dataset):
        super().__init__()
        self.data_var = list(dataset.data_vars.keys())[0]
        for coord in dataset[self.data_var].coords:
            if "amplitudes" in coord:
                self.mw_amplitudes_coord = coord
            elif "repetitions" in coord:
                self.X_repetitions = coord
        self.S21 = dataset[self.data_var].values
        self.independents = dataset[coord].values
        self.fit_results = {}
        self.qubit = dataset[self.data_var].attrs["qubit"]
        dataset[f"y{self.qubit}"].values = np.abs(self.S21)
        self.dataset = dataset

    def analyse_qubit(self):
        mw_amplitude_key = self.mw_amplitudes_coord
        # mw_amplitude_key = 'mw_amplitudes_sweep' + self.qubit
        mw_amplitudes = self.dataset[mw_amplitude_key].size
        sums = []
        for this_amplitude_index in range(mw_amplitudes):
            this_sum = sum(
                np.abs(self.dataset[f"y{self.qubit}"][this_amplitude_index].values)
            )
            sums.append(this_sum)

        index_of_max = np.argmax(np.array(sums))
        self.previous_amplitude = fetch_redis_params("rxy:amp180", self.qubit)
        self.optimal_amp180 = (
            self.dataset[mw_amplitude_key][index_of_max].values
            + self.previous_amplitude
        )
        self.index_of_max = index_of_max

        return [self.optimal_amp180]

    def plotter(self, axis):
        datarray = self.dataset[f"y{self.qubit}"]
        qubit = self.qubit

        datarray.plot(ax=axis, x=f"mw_amplitudes_sweep{qubit}", cmap="RdBu_r")
        axis.set_xlabel("mw amplitude correction")
        axis.axvline(
            # self.dataset[self.mw_amplitudes_coord][self.index_of_max].values,
            self.optimal_amp180 - fetch_redis_params("rxy:amp180", self.qubit),
            c="k",
            lw=4,
            linestyle="--",
        )
