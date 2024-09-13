# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Amr Osman 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import lmfit
import numpy as np
import xarray as xr
from quantify_core.analysis.fitting_models import fft_freq_phase_guess, ExpDecayModel

from tergite_autocalibration.lib.base.analysis import BaseAnalysis
from tergite_autocalibration.lib.nodes.characterization.t1.analysis import cos_func


class T2Model(lmfit.model.Model):
    """
    Generate a cosine model that can be fit to Rabi oscillation data.
    """

    def __init__(self, *args, **kwargs):
        # Pass in the defining equation so the user doesn't have to later.
        super().__init__(cos_func, *args, **kwargs)

        # Enforce oscillation frequency is positive
        self.set_param_hint("frequency", min=0)

        # Fix the phase at pi so that the ouput is at a minimum when drive_amp=0
        self.set_param_hint("phase", min=-0.5, max=0.5)

        # Pi-pulse amplitude can be derived from the oscillation frequency
        self.set_param_hint("duration", expr="1/frequency", vary=False)
        self.set_param_hint("swap", expr="1/(2*frequency)-phase", vary=False)
        self.set_param_hint("cz", expr="2/(2*frequency)-phase", vary=False)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        x = kws.get("x", None)
        if x is None:
            return None

        amp_guess = abs(max(data) - min(data)) / 2  # amp is positive by convention
        offs_guess = np.mean(data)

        # Frequency guess is obtained using a fast fourier transform (FFT).
        (freq_guess, _) = fft_freq_phase_guess(data, x)

        self.set_param_hint("x0", value=x[-1] / 2, min=0)
        self.set_param_hint("frequency", value=freq_guess, min=0)
        self.set_param_hint("amplitude", value=amp_guess, min=-1.5 * amp_guess)
        self.set_param_hint("offset", value=offs_guess)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)


class T2Analysis(BaseAnalysis):
    """
    Analysis that fits an exponential decay function to obtain
    the T2 coherence time from experiment data.
    """

    def __init__(self, dataset: xr.Dataset):
        super().__init__()
        self.dataset = dataset
        self.data_var = list(dataset.data_vars.keys())[0]
        for coord in dataset[self.data_var].coords:
            if "repeat" in coord:
                self.repeat_coord = coord
            elif "delays" in coord:
                self.delays_coord = coord
        self.S21 = dataset[self.data_var].values
        self.delays = dataset[self.delays_coord].values

        self.fit_results = {}
        self.qubit = dataset[self.data_var].attrs["qubit"]

    def analyse_qubit(self):
        model = T2Model()

        delays = self.delays
        self.fit_delays = np.linspace(
            delays[0], delays[-1], 400
        )  # x-values for plotting
        self.T2_times = []
        for indx, repeat in enumerate(self.dataset.coords[self.repeat_coord]):
            complex_values = self.dataset[self.data_var].isel(
                {self.repeat_coord: [indx]}
            )
            magnitudes = np.array(np.absolute(complex_values.values).flat)

            # Gives an initial guess for the model parameters and then fits the model to the data.
            guess = model.guess(data=magnitudes, x=delays)
            fit_result = model.fit(magnitudes, params=guess, x=delays)

            self.fit_delays = np.linspace(delays[0], delays[-1], 400)
            self.fit_y = model.eval(
                fit_result.params, **{model.independent_vars[0]: self.fit_delays}
            )
            self.T2_times.append(fit_result.params["x0"].value)
        self.average_T2 = np.mean(self.T2_times)
        self.error = np.std(self.T2_times)
        return [self.average_T2]

    def plotter(self, ax):
        for indx, repeat in enumerate(self.dataset.coords[self.repeat_coord]):
            complex_values = self.dataset[self.data_var].isel(
                {self.repeat_coord: [indx]}
            )
            magnitudes = np.array(np.absolute(complex_values.values).flat)
            ax.plot(self.delays, magnitudes)
        ax.plot(
            self.fit_delays,
            self.fit_y,
            label=f"Mean T2 = {self.average_T2 * 1e6:.1f} ± {self.error * 1e6:.1f} μs",
        )
        # ax.plot(self.fit_delays, self.fit_y, 'r-', lw=3.0)
        # ax.plot(self.independents, self.magnitudes, 'bo-', ms=3.0)
        ax.set_title(f"T2 experiment for {self.qubit}")
        ax.set_xlabel("Delay (s)")
        ax.set_ylabel("|S21| (V)")

        ax.grid()


class T2EchoAnalysis(BaseAnalysis):
    """
    Analysis that fits an exponential decay function to obtain
    the T1 relaxation time from experiment data.
    """

    def __init__(self, dataset: xr.Dataset):
        super().__init__()
        self.dataset = dataset
        self.data_var = list(dataset.data_vars.keys())[0]
        for coord in dataset[self.data_var].coords:
            if "repeat" in coord:
                self.repeat_coord = coord
            elif "delays" in coord:
                self.delays_coord = coord
        self.S21 = dataset[self.data_var].values
        self.delays = dataset[self.delays_coord].values

        self.fit_results = {}
        self.qubit = dataset[self.data_var].attrs["qubit"]

    def analyse_qubit(self):
        model = ExpDecayModel()

        delays = self.delays
        self.fit_delays = np.linspace(
            delays[0], delays[-1], 400
        )  # x-values for plotting
        self.T2E_times = []
        for indx, repeat in enumerate(self.dataset.coords[self.repeat_coord]):
            complex_values = self.dataset[self.data_var].isel(
                {self.repeat_coord: [indx]}
            )
            magnitudes = np.array(np.absolute(complex_values.values).flat)

            # Gives an initial guess for the model parameters and then fits the model to the data.
            guess = model.guess(data=magnitudes, delay=delays)
            fit_result = model.fit(magnitudes, params=guess, t=delays)
            self.fit_y = model.eval(
                fit_result.params, **{model.independent_vars[0]: self.fit_delays}
            )
            self.T2E_times.append(fit_result.params["tau"].value)
        self.average_T2E = np.mean(self.T2E_times)
        self.error = np.std(self.T2E_times)
        return [self.average_T2E]

    def plotter(self, ax):
        for indx, repeat in enumerate(self.dataset.coords[self.repeat_coord]):
            complex_values = self.dataset[self.data_var].isel(
                {self.repeat_coord: [indx]}
            )
            magnitudes = np.array(np.absolute(complex_values.values).flat)
            ax.plot(self.delays, magnitudes)
        ax.plot(
            self.fit_delays,
            self.fit_y,
            label=f"Mean T2E = {self.average_T2E * 1e6:.1f} ± {self.error * 1e6:.1f} μs",
        )
        # ax.plot(self.fit_delays, self.fit_y, 'r-', lw=3.0)
        # ax.plot(self.independents, self.magnitudes, 'bo-', ms=3.0)
        ax.set_title(f"T2 Echo experiment for {self.qubit}")
        ax.set_xlabel("Delay (s)")
        ax.set_ylabel("|S21| (V)")

        ax.grid()
