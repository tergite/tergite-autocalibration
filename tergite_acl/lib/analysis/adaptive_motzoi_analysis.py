"""
Module containing classes that model, fit and plot data from a Rabi experiment.
"""
import lmfit
import numpy as np
import warnings
from scipy.optimize import root_scalar
import xarray as xr
from quantify_core.analysis.fitting_models import fft_freq_phase_guess
from typing import Callable, Iterable

from tergite_acl.lib.analysis_base import BaseAnalysis


# Cosine function that is fit to Rabi oscillations
def cos_func(
        drive_motzoi: float,
        frequency: float,
        amplitude: float,
        offset: float,
        phase: float,
) -> float:
    return amplitude * np.cos(2 * np.pi * frequency * drive_motzoi + phase) + offset



class MotzoiModel(lmfit.model.Model):
    """
    Generate a cosine model that can be fit to Rabi oscillation data.
    """

    def __init__(self, *args, **kwargs):
        # Pass in the defining equation so the user doesn't have to later.
        super().__init__(cos_func, *args, **kwargs)

        # Enforce oscillation frequency is positive
        self.set_param_hint("frequency", min=0)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        drive_motzoi = kws.get("drive_motzoi", None)
        if drive_motzoi is None:
            return None

        amp_guess = abs(max(data) - min(data)) / 2  # amp is positive by convention
        offs_guess = np.mean(data)

        # Frequency guess is obtained using a fast fourier transform (FFT).
        (freq_guess, _) = fft_freq_phase_guess(data, drive_motzoi)

        self.set_param_hint("frequency", value=freq_guess, min=0)
        self.set_param_hint("amplitude", value=amp_guess, min=0)
        self.set_param_hint("offset", value=offs_guess)
        self.set_param_hint("phase", value=-1.5)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)


class AdaptiveMotzoiAnalysis(BaseAnalysis):
    """
    Analysis that fits a cosine function to Rabi oscillation data.
    """

    def __init__(self, dataset: xr.Dataset):
        super().__init__()
        data_var = list(dataset.data_vars.keys())[0]
        coord = list(dataset[data_var].coords.keys())[0]
        self.S21 = dataset[data_var].values.flatten()
        self.magnitudes = np.absolute(self.S21)
        self.independents = dataset[coord].values
        self.fit_results = {}
        self.qubit = dataset[data_var].attrs['qubit']
        self.samples = 31

    def run_fitting(self, known_values=[]):

        model = MotzoiModel()

        motzois = self.independents

        self.known_values = known_values
        self.fit_motzois = np.linspace(motzois[0], motzois[-1], 400)  # x-values for plotting

        guess = model.guess(self.magnitudes, drive_motzoi=motzois)
        self.fit_result = model.fit(self.magnitudes, params=guess, drive_motzoi=motzois)

        frequency = self.fit_result.params['frequency'].value
        phase = self.fit_result.params['phase'].value

        delta_phi = 2 * np.pi * frequency * (motzois[-1] - motzois[0])
        phi_0 = 2 * np.pi * frequency * motzois[0]
        phi_last = 2 * np.pi * frequency * motzois[-1]

        max_number_of_minimums = 1 + int(delta_phi // (2*np.pi))

        self.min_motzois = []
        for this_min in range(max_number_of_minimums):
            first_extreme_multiple_of_pi =  int(np.abs(phi_0) // np.pi)
            if first_extreme_multiple_of_pi % 2 == 0:
                first_extreme_multiple_of_pi = np.sign(phi_0) * first_extreme_multiple_of_pi
                first_extreme_multiple_of_pi += 1
            else:
                first_extreme_multiple_of_pi = np.sign(phi_0) * first_extreme_multiple_of_pi
            pi_index = first_extreme_multiple_of_pi + this_min * 2
            min_phase = pi_index * np.pi
            if phi_0 < min_phase < phi_last:
                min_motzoi = (min_phase - phase) / ( 2 * np.pi * frequency )
                self.min_motzois.append(min_motzoi)

        self.fit_y = model.eval(self.fit_result.params, **{model.independent_vars[0]: self.fit_motzois})
        if len(self.known_values) == 0:
            self.known_values = self.min_motzois
            self.best_motzoi = None
        else:
            differences = []
            for min_motzoi in self.min_motzois:
                this_differences = np.abs(np.array(self.known_values) - min_motzoi)
                this_min_diffence = np.min(this_differences)
                differences.append(this_min_diffence)

            index_of_best_motzoi = np.argmin(differences)
            self.best_motzoi = self.min_motzois[index_of_best_motzoi]
            self.known_values = [self.best_motzoi]

        return [self.best_motzoi]

    @property
    def updated_qubit_samplespace(self):
        frequency = self.fit_result.params['frequency'].value
        omega = 2 * np.pi * frequency
        phase = self.fit_result.params['phase'].value
        if self.best_motzoi == None:
            phase_of_smallest_minimum = omega * self.min_motzois[0] + phase
            phase_of_largest_minimum = omega * self.min_motzois[-1] + phase
            phase_of_first_sample = phase_of_smallest_minimum - np.pi
            phase_of_last_sample = phase_of_largest_minimum + np.pi
            first_sample = (phase_of_first_sample - phase) / omega
            last_sample = (phase_of_last_sample - phase) / omega
        else:
            phase_of_best_motzoi = omega * self.best_motzoi + phase
            first_sample = (phase_of_best_motzoi - phase - np.pi) / omega
            last_sample = (phase_of_best_motzoi - phase + np.pi) / omega

        qubit_samplespace = {
            'mw_motzois': {
                self.qubit: np.linspace(first_sample, last_sample, self.samples)
            }
        }
        self.first_sample = first_sample
        self.last_sample = last_sample
        return qubit_samplespace

    @property
    def updated_kwargs(self):
        return {'known_values': self.known_values}


    def plotter(self, ax):
        # Plots the data and the fitted model of a Rabi experiment
        for min_motzoi in self.min_motzois:
            ax.axvline(min_motzoi)
        ax.axvline(self.first_sample, c='red')
        ax.axvline(self.last_sample, c='red')
        ax.plot(self.fit_motzois, self.fit_y, 'r-', lw=3.0)
        ax.plot(self.independents, self.magnitudes, 'bo-', ms=3.0)
        ax.set_title(f'Motzois for {self.qubit}')
        ax.set_xlabel('Motzoi parameter (V)')
        ax.set_ylabel('|S21| (V)')
        ax.grid()
