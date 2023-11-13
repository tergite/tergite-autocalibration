"""
Module containing classes that model, fit and plot data
from a qubit (two tone) spectroscopy experiment.
"""
import numpy as np
import xarray as xr
from scipy import signal
import lmfit

# Lorentzian function that is fit to qubit spectroscopy peaks
def loretzian_function( x: float, x0: float, width: float, A: float, c: float,) -> float:
    return A * width**2 / ( (x-x0)**2 + width**2 ) + c


class LorentzianModel(lmfit.model.Model):
    """
    Generate a Lorentzian model that can be fit to qubit spectroscopy data.
    """
    def __init__(self, *args, **kwargs):

        super().__init__(loretzian_function, *args, **kwargs)

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
        #TODO this needs to be checked:
        # width_guess = np.sqrt(width_min * width_max)  # geometric mean, why not?
        width_guess = 0.5e6
        self.set_param_hint("width", value=width_guess)

        # The guess for the vertical offset is the mean absolute value of the data
        c_guess = np.mean(data)
        self.set_param_hint("c", value=c_guess)

        # Calculate A_guess from difference between the peak and the backround level
        A_guess = (np.max(data) - c_guess)
        self.set_param_hint("A", value=A_guess)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)

class QubitSpectroscopyMultidim():
    """
    Analysis that fits a Lorentzian function to qubit spectroscopy data.
    The resulting fit can be analyzed to determine if a peak was found or not.
    """
    def  __init__(self,dataset: xr.Dataset):
        data_var = list(dataset.data_vars.keys())[0]
        self.qubit = dataset[data_var].attrs['qubit']
        self.S21 = dataset[data_var].values
        for coord in dataset[data_var].coords:
            if 'frequencies' in coord: self.frequency_coords = coord
            elif 'amplitudes' in coord: self.amplitude_coords = coord
        dataset[data_var].values = np.abs(self.S21)
        self.frequencies = dataset.coords[self.frequency_coords].values
        self.amplitudes = dataset.coords[self.amplitude_coords].values
        #dataset[f'y{self.qubit}'].values = np.abs(self.S21)
        #breakpoint()

        self.fit_results = {}
        self.data_var = data_var
        self.dataset = dataset

    def run_fitting(self):
        #Initialize the Lorentzian model
        model = LorentzianModel()

        #Fetch the resulting measurement variables from self
        self.magnitudes = np.absolute(self.S21)
        frequencies = self.frequencies
        amplitudes = self.amplitudes

        self.fit_freqs = np.linspace( frequencies[0], frequencies[-1], 500) # x-values for plotting

        qubit_freqs = np.zeros(len(amplitudes))
        peak_magnitudes = np.zeros(len(amplitudes))
        self.fit_y = np.zeros((len(self.fit_freqs),len(amplitudes)))

        for i,a in enumerate(self.amplitudes):
            guess = model.guess(self.magnitudes[:,i], x=frequencies)
            fit_result = model.fit(self.magnitudes[:,i], params=guess, x=frequencies)
            qubit_freqs[i] = fit_result.params['x0'].value
            #self.uncertainty = fit_result.params['x0'].stderr
            self.fit_y[:,i] = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_freqs})
            peak_magnitudes[i] = max(self.fit_y[:,i])

        best_ampl_indx=np.where(peak_magnitudes==max(peak_magnitudes))[0][0]
        self.qubit_ampl = amplitudes[best_ampl_indx]
        self.qubit_freq = qubit_freqs[best_ampl_indx]


        #self.fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_freqs})
        return [self.qubit_freq, self.qubit_ampl]

    def reject_outliers(self, x, m = 3.):
        #Filters out datapoints in x that deviate too far from the median
        d = np.abs(x - np.median(x))
        mdev = np.median(d)
        s = d/mdev if mdev else np.zeros(len(d))
        return x[s<m]

    def has_peak(self, prom_coef: float = 10, wid_coef: float = 2.4, outlier_median: float = 3.):
        # Determines if the data contains one distinct peak or only noise
        x = self.S21
        x_filtered = self.reject_outliers(x, outlier_median)
        peaks, properties=signal.find_peaks(x, prominence=np.std(x_filtered)*prom_coef, width=wid_coef)
        return peaks.size==1

    def plotter(self,ax):
        # Plots the data and the fitted model of a qubit spectroscopy experiment
        #ax.plot( self.fit_freqs, self.fit_y,'r-',lw=3.0)
        self.dataset[self.data_var].plot(ax=ax, x=self.frequency_coords)
        # for i,a in enumerate(self.amplitudes):
        #     if a==self.qubit_ampl:
        #         label=f'Best amplitude:{self.qubit_ampl:.3E}'
        #     else:
        #         label=None
        #     ax.plot(self.fit_freqs, self.fit_y[:,i],'-',lw=3.0, label=label)
        #     ax.plot(self.frequencies, self.magnitudes[:,i],'bo-',ms=3.0)
        #     ax.set_title(f'Amplitude {a}')
        #     ax.set_xlabel('frequency (Hz)')
        #     ax.set_ylabel('|S21| (V)')
        #     ax.grid()
