"""
Module containing classes that model, fit and plot data
from a qubit (two tone) spectroscopy experiment.
"""
import lmfit
import numpy as np
import xarray as xr
from scipy import signal


# Lorentzian function that is fit to qubit spectroscopy peaks
def lorentzian_function(x: float, x0: float, width: float, A: float, c: float, ) -> float:
    return A * width ** 2 / ((x - x0) ** 2 + width ** 2) + c


class LorentzianModel(lmfit.model.Model):
    """
    Generate a Lorentzian model that can be fit to qubit spectroscopy data.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(lorentzian_function, *args, **kwargs)

        self.set_param_hint("x0", vary=True)
        self.set_param_hint("A", vary=True)
        self.set_param_hint("c", vary=True)
        self.set_param_hint("width", vary=True)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        x = kws.get("x", None)

        if x is None:
            return None

        # Guess that the resonance is where the function takes its maximal value
        x0_guess = x[np.argmax(data)]
        self.set_param_hint("x0", value=x0_guess)

        # assume the user isn't trying to fit just a small part of a resonance curve.
        xmin = x.min()
        xmax = x.max()
        width_max = xmax - xmin

        delta_x = np.diff(x)  # assume f is sorted
        min_delta_x = delta_x[delta_x > 0].min()
        # assume data actually samples the resonance reasonably
        width_min = min_delta_x
        # TODO this needs to be checked:
        # width_guess = np.sqrt(width_min * width_max)  # geometric mean, why not?
        width_guess = 0.5e6
        self.set_param_hint("width", value=width_guess)

        # The guess for the vertical offset is the mean absolute value of the data
        c_guess = np.mean(data)
        self.set_param_hint("c", value=c_guess)

        # Calculate A_guess from difference between the peak and the backround level
        A_guess = (np.max(data) - c_guess) / 10
        self.set_param_hint("A", value=A_guess)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)


class QubitSpectroscopyAnalysis():
    """
    Analysis that fits a Lorentzian function to qubit spectroscopy data.
    The resulting fit can be analyzed to determine if a peak was found or not.
    """

    def __init__(self, dataset: xr.Dataset):
        data_var = list(dataset.data_vars.keys())[0]
        for coord in dataset[data_var].coords:
            if 'frequencies' in coord:
                self.frequencies = coord
            elif 'currents' in coord:
                self.currents = coord
        self.S21 = dataset[data_var].values
        self.independents = dataset[self.frequencies].values
        self.fit_results = {}
        self.qubit = dataset[data_var].attrs['qubit']

    def run_fitting(self):

        # Fetch the resulting measurement variables
        self.magnitudes = np.abs(self.S21)
        frequencies = self.independents

        if not self.has_peak():
            return [np.mean(frequencies)]

        self.fit_freqs = np.linspace(frequencies[0], frequencies[-1], 500)  # x-values for plotting

        # Initialize the Lorentzian model
        model = LorentzianModel()

        # Gives an initial guess for the model parameters and then fits the model to the data.
        guess = model.guess(self.magnitudes, x=frequencies)
        fit_result = model.fit(self.magnitudes, params=guess, x=frequencies)

        self.freq = fit_result.params['x0'].value
        self.uncertainty = fit_result.params['x0'].stderr

        self.fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_freqs})

        # # Take maximal value directly
        # self.max_freq = frequencies[np.argmax(self.magnitudes)]
        # # print(self.max_freq)
        # return [self.max_freq]
        return [self.freq]

    def reject_outliers(self, data, m=3.):
        # Filters out datapoints in data that deviate too far from the median
        shifted_data = np.abs(data - np.median(data))
        mdev = np.median(shifted_data)
        s = shifted_data / mdev if mdev else np.zeros(len(shifted_data))
        filtered_data = data[s < m]
        return filtered_data

    def has_peak(self, prom_coef: float = 6, wid_coef: float = 2.4, outlier_median: float = 3.):
        # Determines if the data contains one distinct peak or only noise
        x = np.abs(self.S21)
        x_filtered = self.reject_outliers(x, outlier_median)
        self.filtered_std = np.std(x_filtered)
        peaks, properties = signal.find_peaks(
            x, prominence=self.filtered_std * prom_coef, width=wid_coef
        )
        self.prominence = properties["prominences"][0] if len(properties['prominences']) == 1 else 0
        self.hasPeak = peaks.size == 1
        self.hasPeak = True
        return self.hasPeak

    def plotter(self, ax):
        # Plots the data and the fitted model of a qubit spectroscopy experiment
        if self.hasPeak:
            ax.plot(self.fit_freqs, self.fit_y, 'r-', lw=3.0)
            min = np.min(self.magnitudes)
            # ax.vlines(self.freq, min, self.prominence + min, lw=4, color='teal')
            # ax.vlines(self.freq-1e6, min, self.filtered_std + min, lw=4, color='orange')
            ax.plot(self.fit_freqs, self.fit_y, 'r-', lw=3.0,
                    label=f"freq = {self.freq:.6E} ± {self.uncertainty:.1E} (Hz)")
        ax.plot(self.independents, self.magnitudes, 'bo-', ms=3.0)
        ax.set_title(f'Qubit Spectroscopy for {self.qubit}')
        ax.set_xlabel('frequency (Hz)')
        ax.set_ylabel('|S21| (V)')
        ax.grid()
