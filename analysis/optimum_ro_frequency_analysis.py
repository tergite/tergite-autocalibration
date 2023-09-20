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
        data_var = list(dataset.data_vars.keys())[0]
        self.S21_0 = dataset[data_var][0].values
        self.S21_1 = dataset[data_var][1].values

        for coord in dataset.coords:
            if 'frequencies' in str(coord):
                self.frequencies = dataset[coord].values

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

        distances = self.fit_IQ_1 - self.fit_IQ_0
        self.index_of_max_distance = np.argmax(np.abs(distances))
        self.optimal_frequency = fit_frequencies[self.index_of_max_distance]

        return self.optimal_frequency

    def plotter(self,ax):
        ax.set_xlabel('I quadrature (V)')
        ax.set_ylabel('Q quadrature (V)')
        ax.plot(self.fit_IQ_0.real, self.fit_IQ_0.imag)
        ax.plot(self.fit_IQ_1.real, self.fit_IQ_1.imag)
        f0 = self.fit_IQ_0[self.index_of_max_distance]
        f1 = self.fit_IQ_1[self.index_of_max_distance]

        ax.scatter([f0.real, f1.real], [f0.imag, f1.imag], marker='*', label=f'opt_freq: {self.optimal_frequency}')
        # ax.axvline(self.minimum_freq,c='blue',ls='solid',label='frequency at min')
        ax.grid()
