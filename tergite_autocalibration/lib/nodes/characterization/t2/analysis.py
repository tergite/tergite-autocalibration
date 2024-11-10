# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
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
from quantify_core.analysis.fitting_models import fft_freq_phase_guess, ExpDecayModel

from tergite_autocalibration.lib.base.analysis import (
    BaseQubitAnalysis,
    BaseAllQubitsRepeatAnalysis,
)
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


from abc import ABC, abstractmethod


class BaseT2QubitAnalysis(BaseQubitAnalysis, ABC):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.T2_times = []

    def analyse_qubit(self):
        self._identify_coords()
        self.fit_delays = np.linspace(self.delays[0], self.delays[-1], 400)
        for indx in range(len(self.dataset.coords[self.repeat_coord])):
            magnitudes_flat = self._get_magnitudes(indx)
            fit_result = self.fit_model(magnitudes_flat)

            self.fit_y = self.model.eval(
                fit_result.params, **{self.model.independent_vars[0]: self.fit_delays}
            )
            self.T2_times.append(self._extract_t2_time(fit_result))

        self.average_T2 = np.mean(self.T2_times)
        self.error = np.std(self.T2_times)
        return [self.average_T2]

    @abstractmethod
    def fit_model(self, magnitudes_flat):
        pass

    @abstractmethod
    def _extract_t2_time(self, fit_result):
        pass

    def _identify_coords(self):
        for coord in self.dataset[self.data_var].coords:
            if "repeat" in coord:
                self.repeat_coord = coord
            elif "delays" in coord:
                self.delays_coord = coord
        self.delays = self.dataset[self.delays_coord].values

    def _get_magnitudes(self, indx):
        magnitudes = self.magnitudes[self.data_var].isel({self.repeat_coord: indx})
        return magnitudes.values.flatten()

    def plotter(self, ax):
        for indx in range(len(self.dataset.coords[self.repeat_coord])):
            magnitudes_flat = self._get_magnitudes(indx)
            ax.plot(self.delays, magnitudes_flat)
        ax.plot(
            self.fit_delays,
            self.fit_y,
            label=f"Mean T2 = {self.average_T2 * 1e6:.1f} ± {self.error * 1e6:.1f} μs",
        )
        ax.set_title(f"T2 experiment for {self.qubit}")
        ax.set_xlabel("Delay (s)")
        ax.set_ylabel("|S21| (V)")
        ax.grid()


class T2QubitAnalysis(BaseT2QubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.model = T2Model()

    def fit_model(self, magnitudes_flat):
        guess = self.model.guess(data=magnitudes_flat, x=self.delays)
        return self.model.fit(magnitudes_flat, params=guess, x=self.delays)

    def _extract_t2_time(self, fit_result):
        return fit_result.params["x0"].value


class T2EchoQubitAnalysis(BaseT2QubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.model = ExpDecayModel()

    def fit_model(self, magnitudes_flat):
        guess = self.model.guess(data=magnitudes_flat, delay=self.delays)
        return self.model.fit(magnitudes_flat, params=guess, t=self.delays)

    def _extract_t2_time(self, fit_result):
        return fit_result.params["tau"].value


class T2NodeAnalysis(BaseAllQubitsRepeatAnalysis):
    single_qubit_analysis_obj = T2QubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.repeat_coordinate_name = "repeat"


class T2EchoNodeAnalysis(BaseAllQubitsRepeatAnalysis):
    single_qubit_analysis_obj = T2EchoQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.repeat_coordinate_name = "repeat"
