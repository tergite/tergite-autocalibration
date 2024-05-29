"""
Module containing classes that model, fit and plot data from a Rabi experiment.
"""
import lmfit
import numpy as np
import xarray as xr
from quantify_core.analysis.fitting_models import fft_freq_phase_guess

from tergite_calibration.lib.analysis_base import BaseAnalysis


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
        self.qubit = dataset[data_var].attrs['qubit']

    def run_fitting(self):
        # Initialize the Rabi model
        model = RabiModel()

        # Fetch the resulting measurement variables from self
        self.magnitudes = np.absolute(self.S21)
        amplitudes = self.independents

        self.fit_amplitudes = np.linspace(amplitudes[0], amplitudes[-1], 400)  # x-values for plotting

        # Gives an initial guess for the model parameters and then fits the model to the data.
        guess = model.guess(self.magnitudes, drive_amp=amplitudes)
        fit_result = model.fit(self.magnitudes, params=guess, drive_amp=amplitudes)

        self.ampl = fit_result.params['amp180'].value
        self.uncertainty = fit_result.params['amp180'].stderr

        print(f'{ self.ampl = }')
        print(f'{ self.uncertainty = }')

        self.fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_amplitudes})
        return [self.ampl]

    def plotter(self, ax):
        # Plots the data and the fitted model of a Rabi experiment
        ax.plot(self.fit_amplitudes, self.fit_y, 'r-', lw=3.0, label=f" π_ampl = {self.ampl:.2E} (V)")
        ax.plot(self.independents, self.magnitudes, 'bo-', ms=3.0)
        ax.set_title(f'Rabi Oscillations for {self.qubit}')
        ax.set_xlabel('Amplitude (V)')
        ax.set_ylabel('|S21| (V)')
        ax.grid()
