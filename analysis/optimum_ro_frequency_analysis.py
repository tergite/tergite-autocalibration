"""
Module containing a class that fits data from a resonator spectroscopy experiment.
"""
import numpy as np
from quantify_core.analysis import fitting_models as fm
import redis
import xarray as xr

model = fm.ResonatorModel()
redis_connection = redis.Redis(decode_responses=True)

class OptimalROFrequencyAnalysis():
    """
    Analysis that fits the data of resonator spectroscopy experiments
    and extractst the optimal RO frequency.
    """
    def __init__(self, dataset: xr.Dataset):
        data_var = dataset.data_vars.keys()

        for data_var in dataset.data_vars:
            var = dataset[data_var]
            if var.attrs['qubit_state'] == 0:
                self.S21_0 = var.values
            elif  var.attrs['qubit_state'] == 1:
                self.S21_1 = var.values
            else :
               raise ValueError('Invalid state')

        self.frequencies = list(dataset.coords.values())[0].values

        self.fit_results = {}

    def run_fitting(self):
        # Gives an initial guess for the model parameters and then fits the model to the data.
        guess_0 = model.guess(self.S21_0, f=self.frequencies)
        guess_1 = model.guess(self.S21_1, f=self.frequencies)
        fit_frequencies = np.linspace(self.frequencies[0], self.frequencies[-1], 400)
        self.fit_result_0 = model.fit(self.S21_0, params=guess_0, f=self.frequencies)
        self.fit_result_1 = model.fit(self.S21_1, params=guess_1, f=self.frequencies)
        self.fit_IQ_0 = model.eval(self.fit_result_0.params, f=fit_frequencies)
        self.fit_IQ_1 = model.eval(self.fit_result_1.params, f=fit_frequencies)

        fit_values_0 = self.fit_result_0.values
        fit_values_1 = self.fit_result_1.values

        # fitted_resonator_frequency = fit_fr = fit_values['fr']
        # fit_Ql = fit_values['Ql']
        # fit_Qe = fit_values['Qe']
        # fit_ph = fit_values['theta']
        # # analytical expression, probably an interpolation of the fit would be better
        # self.minimum_freq = fit_fr / (4*fit_Qe*fit_Ql*np.sin(fit_ph)) * (
        #                 4*fit_Qe*fit_Ql*np.sin(fit_ph)
        #               - 2*fit_Qe*np.cos(fit_ph)
        #               + fit_Ql
        #               + np.sqrt(  4*fit_Qe**2
        #                         - 4*fit_Qe*fit_Ql*np.cos(fit_ph)
        #                         + fit_Ql**2 )
        #               )
        # return self.minimum_freq
        return 0

    def plotter(self,ax):
        ax.set_xlabel('I quadrature (V)')
        ax.set_ylabel('Q quadrature (V)')
        ax.plot(self.fit_IQ_0.real, self.fit_IQ_0.imag)
        ax.plot(self.fit_IQ_1.real, self.fit_IQ_1.imag)
        # ax.axvline(self.minimum_freq,c='blue',ls='solid',label='frequency at min')
        ax.grid()

#class ResonatorSpectroscopy_1_Analysis(ResonatorSpectroscopyAnalysis):
#    def __init__(self, dataset: xr.Dataset):
#        self.dataset = dataset
#        super().__init__(self.dataset)
#    def plotter(self,ax):
#        #breakpoint()
#        this_qubit = self.dataset.attrs['qubit']
#        ax.set_xlabel('Frequency (Hz)')
#        ax.set_ylabel('|S21| (V)')
#        ro_freq = float(redis_connection.hget(f'transmons:{this_qubit}', 'ro_freq'))
#        self.fitting_model.plot_fit(ax,numpoints = 400,xlabel=None, title=None)
#        ax.axvline(self.minimum_freq,c='green',ls='solid',label='frequency |1> ')
#        ax.axvline(ro_freq,c='blue',ls='dashed',label='frequency |0>')
#        ax.grid()
#
#class ResonatorSpectroscopy_2_Analysis(ResonatorSpectroscopyAnalysis):
#    def __init__(self, dataset: xr.Dataset):
#        self.dataset = dataset
#        super().__init__(self.dataset)
#    def plotter(self,ax):
#        this_qubit = self.dataset.attrs['qubit']
#        ax.set_xlabel('Frequency (Hz)')
#        ax.set_ylabel('|S21| (V)')
#        ro_freq = float(redis_connection.hget(f'transmons:{this_qubit}', 'ro_freq'))
#        ro_freq_1 = float(redis_connection.hget(f'transmons:{this_qubit}', 'ro_freq_1'))
#        self.fitting_model.plot_fit(ax,numpoints = 400,xlabel=None, title=None)
#        ax.axvline(self.minimum_freq,c='red',ls='solid',label='frequency |2>')
#        ax.axvline(ro_freq_1,c='green',ls='dashed',label='frequency |1>')
#        ax.axvline(ro_freq,c='blue',ls='dashed',label='frequency |0>')
#        ax.grid()
