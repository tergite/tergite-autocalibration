import numpy as np
from quantify_core.analysis import fitting_models as fm
import redis
import xarray as xr

model = fm.ResonatorModel()
redis_connection = redis.Redis(decode_responses=True)

class ResonatorSpectroscopyAnalysis():
    def __init__(self, dataset: xr.Dataset):
        data_var = list(dataset.data_vars.keys())[0]
        coord = list(dataset[data_var].coords.keys())[0]

        self.S21 = dataset[data_var].values
        self.frequencies = dataset[coord].values
        self.fit_results = {}

    def run_fitting(self):
        S21 = self.S21
        frequencies = self.frequencies
        guess = model.guess(S21, f=frequencies)

        self.fitting_model = model.fit(S21, params=guess, f=frequencies)

        fit_result = self.fitting_model.values

        fitted_resonator_frequency = fit_fr = fit_result['fr']
        fit_Ql = fit_result['Ql']
        fit_Qe = fit_result['Qe']
        fit_ph = fit_result['theta']

        # analytical expression, probably an interpolation of the fit would be better
        self.minimum_freq = fit_fr / (4*fit_Qe*fit_Ql*np.sin(fit_ph)) * (
                        4*fit_Qe*fit_Ql*np.sin(fit_ph)
                      - 2*fit_Qe*np.cos(fit_ph)
                      + fit_Ql
                      + np.sqrt(  4*fit_Qe**2
                                - 4*fit_Qe*fit_Ql*np.cos(fit_ph)
                                + fit_Ql**2 )
                      )
        return self.minimum_freq

    def plotter(self,ax):
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('|S21| (V)')
        self.fitting_model.plot_fit(ax,numpoints = 400,xlabel=None, title=None)
        ax.axvline(self.minimum_freq,c='blue',ls='solid',label='frequency at min')
        ax.grid()

class ResonatorSpectroscopy_1_Analysis(ResonatorSpectroscopyAnalysis):
    def __init__(self, dataset: xr.Dataset):
        self.dataset = dataset
        super().__init__(self.dataset)
    def plotter(self,ax):
        this_qubit = self.dataset.attrs['qubit']
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('|S21| (V)')
        ro_freq = redis_connection.hget(f'transmons:{this_qubit}', 'ro_freq')
        self.fitting_model.plot_fit(ax,numpoints = 400,xlabel=None, title=None)
        ax.axvline(self.minimum_freq,c='blue',ls='solid',label='frequency |1> ')
        ax.axvline(ro_freq,c='green',ls='solid',label='frequency |0>')
        ax.grid()
