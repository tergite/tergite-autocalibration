# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Amr Osman 2024
# (C) Copyright Michele Faucci Giannelli 2024, 2025
# (C) Copyright Theresa Fuchs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from abc import ABC, abstractmethod
import lmfit
from matplotlib.axes import Axes
import numpy as np
from quantify_core.analysis.fitting_models import ExpDecayModel, fft_freq_phase_guess

from tergite_autocalibration.lib.base.analysis import (
    BaseAllQubitsAnalysis,
    BaseQubitAnalysis,
)
from tergite_autocalibration.utils.dto.qoi import QOI


def cos_func(
    x: float,
    frequency: float,
    amplitude: float,
    offset: float,
    x0: float,
    phase: float = 0,
) -> float:
    """
    Generate a cosine function with exponential decay.
    Args:
        x (float): The input value.
        frequency (float): The frequency of the cosine wave.
        amplitude (float): The amplitude of the cosine wave.
        offset (float): The offset to be added to the cosine wave.
        x0 (float): The decay constant for the exponential decay.
        phase (float, optional): The phase shift of the cosine wave. Defaults to 0.
    Returns:
        float: The value of the cosine function with exponential decay at x.
    """

    return (
        amplitude * np.cos(2 * np.pi * frequency * (x + phase)) * np.exp(-x / x0)
        + offset
    )


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


class BaseT2QubitAnalysis(BaseQubitAnalysis, ABC):
    """
    Base class for T2 qubit analysis.
    This class provides the structure for analyzing T2 times
    for a single qubit. It should be subclassed to implement
    specific fitting models and extraction methods.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.t2_times = []
        self.average_t2 = None
        self.error = None
        self.delays_coord = None
        self.repeat_coord = None
        self.delays = None
        self.fit_delays = None
        self.fit_y = None
        self.offset_times = []
        self.amplitude_times = []
        self.frequency_times = []
        self.phase_times = []
        self.average_offset = None
        self.average_amplitude = None
        self.average_frequency = None
        self.average_phase = None
        self.average_t2_y = None
        self.label = ""
        self.param_name = ""
        self.model = None  # This will be set in the subclass
        self.average_params = None  # This will be set after fitting

    def analyse_t2_times(self):
        """
        Perform the analysis of T2 times for the qubit.
        This method identifies the coordinates for delays and repetitions,
        extracts the magnitudes for each repetition, fits the model,
        and calculates the average T2 time and its error.
        """

        self._identify_coords()
        self.fit_delays = np.linspace(self.delays[0], self.delays[-1], 400)
        for indx in range(len(self.dataset.coords[self.repeat_coord])):
            magnitudes_flat = self._get_magnitudes(indx)
            fit_result = self.fit_model(magnitudes_flat)

            self.fit_y = self.model.eval(
                fit_result.params, **{self.model.independent_vars[0]: self.fit_delays}
            )
            self.t2_times.append(fit_result.params[self.param_name].value)
            self.offset_times.append(fit_result.params["offset"].value)
            self.amplitude_times.append(fit_result.params["amplitude"].value)
            if "frequency" in fit_result.params:
                self.frequency_times.append(fit_result.params["frequency"].value)
                self.phase_times.append(fit_result.params["phase"].value)

        self.average_t2 = np.mean(self.t2_times)
        self.error = np.std(self.t2_times)

        self.average_offset = np.mean(self.offset_times)
        self.average_amplitude = np.mean(self.amplitude_times)
        if len(self.frequency_times) > 0:
            self.average_frequency = np.mean(self.frequency_times)
            self.average_phase = np.mean(self.phase_times)

        # Prepare base params object for evaluating mean fit
        self.average_params = fit_result.params.copy()
        self.average_params[self.param_name].value = self.average_t2
        self.average_params["offset"].value = self.average_offset
        self.average_params["amplitude"].value = self.average_amplitude

        # Evaluate upper and lower bands

        self.average_t2_y = self.model.eval(
            params=self.average_params,
            **{self.model.independent_vars[0]: self.fit_delays},
        )

    # what are all these?
    @abstractmethod
    def fit_model(self, magnitudes_flat):
        pass

    def _identify_coords(self):
        for coord in self.dataset[self.data_var].coords:
            if "repeat" in coord:
                self.repeat_coord = coord
            elif "delays" in coord:
                self.delays_coord = coord
        self.delays = (
            self.dataset[self.delays_coord].values * 1e6
        )  # Convert delays to microseconds

    def _get_magnitudes(self, indx):
        magnitudes = self.magnitudes[self.data_var].isel({self.repeat_coord: indx})
        return magnitudes.values.flatten() * 1e6  # Convert to microseconds

    def plotter(self, ax):
        for indx in range(len(self.dataset.coords[self.repeat_coord])):
            magnitudes_flat = self._get_magnitudes(indx)
            ax.plot(self.delays, magnitudes_flat, alpha=0.3)

        ax.plot(
            self.fit_delays,
            self.average_t2_y,
            color="red",
            label=f"Mean {self.label} = {self.average_t2 * 1e6:.1f} ± {self.error * 1e6:.1f} μs",
        )
        ax.set_title(f"T2 for {self.qubit}")
        ax.set_xlabel("Delay (μs)")
        ax.set_ylabel("|S21| (V)")
        ax.legend()
        ax.grid()


class T2QubitAnalysis(BaseT2QubitAnalysis):
    """
    Class for T2 qubit analysis.
    This class implements the analysis of T2 times for a single qubit
    using a cosine model with exponential decay.
    It fits the model to the data and extracts the T2 time.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.model = T2Model()
        self.label = "T2"
        self.param_name = "x0"

    def analyse_qubit(self):
        self.analyse_t2_times()
        analysis_succesful = True
        analysis_result = {
            "t2_time": {
                "value": self.average_t2,
                "error": self.error,
            }
        }
        qoi = QOI(analysis_result, analysis_succesful)
        return qoi

    def fit_model(self, magnitudes_flat):
        guess = self.model.guess(data=magnitudes_flat, x=self.delays)
        return self.model.fit(magnitudes_flat, params=guess, x=self.delays)


class T2EchoQubitAnalysis(BaseT2QubitAnalysis):
    """
    Class for T2 Echo qubit analysis.
    This class implements the analysis of T2 Echo times for a single qubit
    using an exponential decay model.
    It fits the model to the data and extracts the T2 Echo time.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.model = ExpDecayModel()
        self.label = "T2 Echo"
        self.param_name = "tau"

    def analyse_qubit(self):
        self.analyse_t2_times()
        analysis_succesful = True
        analysis_result = {
            "t2_echo_time": {
                "value": self.average_t2,
                "error": self.error,
            }
        }
        qoi = QOI(analysis_result, analysis_succesful)
        return qoi

    def fit_model(self, magnitudes_flat):
        guess = self.model.guess(data=magnitudes_flat, delay=self.delays)
        return self.model.fit(magnitudes_flat, params=guess, t=self.delays)

    def plotter(self, ax: Axes):
        super().plotter(ax)

        params_upper = self.average_params.copy()
        params_upper["tau"].value = self.average_t2 + self.error
        average_t2_upper = self.model.eval(params=params_upper, t=self.fit_delays)

        params_lower = self.average_params.copy()
        params_lower["tau"].value = self.average_t2 - self.error
        average_t2_lower = self.model.eval(params=params_lower, t=self.fit_delays)

        ax.fill_between(
            self.fit_delays,
            average_t2_lower,
            average_t2_upper,
            color="red",
            alpha=0.2,
            label="±1σ",
        )


class T2NodeAnalysis(BaseAllQubitsAnalysis):
    """
    Node analysis for T2 measurements.
    This class performs T2 analysis for multiple qubits
    and uses the T2QubitAnalysis class for individual qubit analysis.
    """

    single_qubit_analysis_obj = T2QubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)


class T2EchoNodeAnalysis(BaseAllQubitsAnalysis):
    """
    Node analysis for T2 Echo measurements.
    This class performs T2 Echo analysis for multiple qubits
    and uses the T2EchoQubitAnalysis class for individual qubit analysis.
    """

    single_qubit_analysis_obj = T2EchoQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
