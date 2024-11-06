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

import lmfit
import numpy as np
import xarray as xr
from quantify_core.analysis.fitting_models import (
    exp_damp_osc_func,
    fft_freq_phase_guess,
)

from tergite_autocalibration.config.settings import REDIS_CONNECTION
from ....base.analysis import BaseAllQubitsAnalysis, BaseQubitAnalysis


class RamseyModel(lmfit.model.Model):
    def __init__(self, *args, **kwargs):
        # pass in the defining equation so the user doesn't have to later.
        super().__init__(exp_damp_osc_func, *args, **kwargs)

        # Enforce oscillation frequency is positive
        self.set_param_hint("frequency", min=0)
        # Enforce amplitude is positive
        self.set_param_hint("amplitude", min=0)
        # Enforce decay time is positive
        self.set_param_hint("tau", min=0)

        # Fix the n_factor at 1
        self.set_param_hint("n_factor", expr="1", vary=False)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        t = kws.get("t", None)
        if t is None:
            raise ValueError(
                'Time variable "t" must be specified in order to guess parameters'
            )

        amp_guess = abs(max(data) - min(data)) / 2  # amp is positive by convention
        exp_offs_guess = np.mean(data)
        tau_guess = 2 / 3 * np.max(t)

        (freq_guess, phase_guess) = fft_freq_phase_guess(data, t)

        self.set_param_hint("frequency", value=freq_guess, min=0)
        self.set_param_hint("amplitude", value=amp_guess, min=0)
        self.set_param_hint("offset", value=exp_offs_guess)
        self.set_param_hint("phase", value=phase_guess)
        self.set_param_hint("tau", value=tau_guess, min=0)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)


class RamseyDetuningsBaseQubitAnalysis(BaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.redis_field = ""

    def analyse_qubit(self):
        for coord in self.dataset[self.data_var].coords:
            if "delay" in coord:
                self.delay_coord = coord
            elif "detuning" in coord:
                self.detuning_coord = coord
        self.artificial_detunings = self.dataset.coords[self.detuning_coord].values
        redis_key = f"transmons:{self.qubit}"
        redis_value = REDIS_CONNECTION.hget(f"{redis_key}", self.redis_field)
        self.qubit_frequency = float(redis_value)

        self.fit_results = {}

        model = RamseyModel()
        ramsey_delays = self.dataset.coords[self.delay_coord].values
        self.fit_ramsey_delays = np.linspace(ramsey_delays[0], ramsey_delays[-1], 400)

        # ToDo: make this a data member and plot all nested fits
        fits = []
        for indx, detuning in enumerate(self.dataset.coords[self.detuning_coord]):
            complex_values = self.magnitudes[self.data_var].isel(
                {self.detuning_coord: [indx]}
            )
            magnitudes = np.array(np.absolute(complex_values.values).flat)
            guess = model.guess(magnitudes, t=ramsey_delays)
            fit_result = model.fit(magnitudes, params=guess, t=ramsey_delays)
            fit_y = model.eval(
                fit_result.params, **{model.independent_vars[0]: self.fit_ramsey_delays}
            )
            fitted_detuning = fit_result.params["frequency"].value
            fits.append(fitted_detuning)
        fits = np.array(fits)
        index_of_min = np.argmin(fits)
        self.fitted_detunings = np.concatenate(
            (fits[:index_of_min] * (-1), fits[index_of_min:])
        )

        m, b = np.polyfit(self.artificial_detunings, self.fitted_detunings, 1)
        self.poly1d_fn = np.poly1d((m, b))
        self.frequency_correction = -b / m

        self.corrected_qubit_frequency = (
            self.qubit_frequency + self.frequency_correction
        )
        return [self.corrected_qubit_frequency]

    def plotter(self, ax):
        ax.plot(self.artificial_detunings, self.fitted_detunings, "bo", ms=5.0)
        ax.axvline(
            self.frequency_correction,
            color="red",
            label=f"correction: {int(self.frequency_correction) / 1e3} kHz",
        )
        ax.plot(
            self.artificial_detunings,
            self.poly1d_fn(self.artificial_detunings),
            "--b",
            lw=1,
        )
        ax.axvline(0, color="black", lw=1)
        ax.set_xlabel("Artificial detuning (Hz)")
        ax.set_ylabel("Fitted detuning (Hz)")

        ax.grid()


class RamseyDetunings01QubitAnalysis(RamseyDetuningsBaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.redis_field = "clock_freqs:f01"


class RamseyDetunings12QubitAnalysis(RamseyDetuningsBaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.redis_field = "clock_freqs:f12"


class RamseyDetunings01NodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = RamseyDetunings01QubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)


class RamseyDetunings12NodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = RamseyDetunings12QubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
