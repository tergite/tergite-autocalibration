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

"""
Module containing classes that model, fit and plot data from a Rabi experiment.
"""
import lmfit
import numpy as np
from quantify_core.analysis.fitting_models import fft_freq_phase_guess

from tergite_autocalibration.lib.base.analysis import (
    BaseAllQubitsAnalysis,
    BaseQubitAnalysis,
)
from tergite_autocalibration.utils.backend.redis_utils import fetch_redis_params


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


class RabiQubitAnalysis(BaseQubitAnalysis):
    """
    Analysis that fits a cosine function to Rabi oscillation data.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def analyse_qubit(self):
        model = RabiModel()

        for coord in self.dataset.coords:
            if "amplitudes" in coord:
                self.amplitude_coord = coord
                self.amplitudes = self.dataset[coord].values
            else:
                raise ValueError("Invalid Coordinate")

        self.fit_plot_amplitudes = np.linspace(
            self.amplitudes[0], self.amplitudes[-1], 400
        )  # x-values for plotting

        # Gives an initial guess for the model parameters and then fits the model to the data.
        guess = model.guess(
            self.magnitudes[self.data_var].values, drive_amp=self.amplitudes
        )
        fit_result = model.fit(
            self.magnitudes[self.data_var].values,
            params=guess,
            drive_amp=self.amplitudes,
        )

        self.pi_amplitude = fit_result.params["amp180"].value
        self.uncertainty = fit_result.params["amp180"].stderr
        self.scaled_uncertainty = self.uncertainty / self.pi_amplitude

        self.fit_y = model.eval(fit_result.params, drive_amp=self.fit_plot_amplitudes)

        if self.scaled_uncertainty < 2e-2 and self.pi_amplitude < 0.95:
            analysis_succesful = True
        else:
            analysis_succesful = False

        analysis_result = {
            "rxy:amp180": {
                "value": self.pi_amplitude,
                "error": self.scaled_uncertainty,
            }
        }

        qoi = QOI(analysis_result, analysis_succesful)

        return qoi

    def plotter(self, ax):
        ax.plot(
            self.fit_plot_amplitudes,
            self.fit_y,
            "r-",
            lw=3.0,
            label=f"π_ampl = {self.pi_amplitude:.2E}"
            r"$\pm$"
            f"{self.uncertainty:.2E}(V)\n"
            f"scaled uncertainty: {self.scaled_uncertainty:.2E}",
        )

        ax.plot(self.amplitudes, self.magnitudes[self.data_var].values, "bo-", ms=3.0)
        ax.set_title(f"Rabi Oscillations for {self.qubit}")
        ax.set_xlabel("Amplitude (V)")
        ax.set_ylabel("|S21| (V)")
        ax.grid()


class RabiNodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = RabiQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)


class NRabiQubitAnalysis(BaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def analyse_qubit(self):
        for coord in self.dataset[self.data_var].coords:
            if "amplitudes" in coord:
                self.mw_amplitudes_coord = coord
            elif "repetitions" in coord:
                self.x_repetitions_coord = coord

        mw_amplitude_key = self.mw_amplitudes_coord
        mw_amplitudes = self.magnitudes[mw_amplitude_key].size
        sums = []
        for this_amplitude_index in range(mw_amplitudes):
            this_sum = sum(self.magnitudes[self.data_var][this_amplitude_index].values)
            sums.append(this_sum)

        index_of_min = np.argmin(np.array(sums))
        self.previous_amplitude = fetch_redis_params("rxy:amp180", self.qubit)
        self.optimal_amp180 = (
            self.magnitudes[mw_amplitude_key][index_of_min].values.item()
            + self.previous_amplitude
        )
        self.index_of_max = index_of_min
        self.shift = self.magnitudes[mw_amplitude_key][index_of_min].values

        analysis_succesful = True

        analysis_result = {
            "rxy:amp180": {
                "value": self.optimal_amp180,
                "error": 0,
            }
        }

        qoi = QOI(analysis_result, analysis_succesful)

        return qoi

    def plotter(self, axis):
        datarray = self.magnitudes[self.data_var]

        datarray.plot(ax=axis, x=f"mw_amplitudes_sweep{self.qubit}", cmap="RdBu_r")
        axis.set_xlabel("mw amplitude correction")
        line = self.shift

        axis.axvline(
            line,
            c="k",
            lw=4,
            linestyle="--",
        )


class NRabiNodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = NRabiQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
