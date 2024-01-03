"""
Module containing a class that fits data from a resonator spectroscopy experiment.
"""
import numpy as np
from quantify_core.analysis import fitting_models as fm
import redis
import xarray as xr
redis_connection = redis.Redis(decode_responses=True)

model = fm.ResonatorModel()
redis_connection = redis.Redis(decode_responses=True)

class OptimalROFrequencyAnalysis():
    """
    Analysis that fits the data of resonator spectroscopy experiments
    and extractst the optimal RO frequency.
    """
    def __init__(self, dataset: xr.Dataset):
        self.dataset = dataset
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

        return [self.optimal_frequency]

    def plotter(self,ax):
        this_qubit = self.dataset.attrs['qubit']
        ax.set_xlabel('I quadrature (V)')
        ax.set_ylabel('Q quadrature (V)')
        ax.plot(self.fit_IQ_0.real, self.fit_IQ_0.imag)
        ax.plot(self.fit_IQ_1.real, self.fit_IQ_1.imag)
        f0 = self.fit_IQ_0[self.index_of_max_distance]
        f1 = self.fit_IQ_1[self.index_of_max_distance]

        ro_freq = float(redis_connection.hget(f'transmons:{this_qubit}', 'ro_freq'))
        ro_freq_1 = float(redis_connection.hget(f'transmons:{this_qubit}', 'ro_freq_1'))

        label_text = f'opt_ro: {int(self.optimal_frequency)}\n' 
        label_text = f'opt_ro: |0>_ro: {int(ro_freq)}\n|1>_ro: {int(ro_freq_1)}' 

        ax.scatter(
            [f0.real, f1.real], [f0.imag, f1.imag], 
            marker='*',c='red', s=64,  label=label_text
        )
        ax.grid()

class OptimalRO_012_FrequencyAnalysis(OptimalROFrequencyAnalysis):
    def __init__(self, dataset: xr.Dataset):
        self.dataset = dataset
        data_var = list(dataset.data_vars.keys())[0]
        self.S21_2 = dataset[data_var][2].values
        super().__init__(self.dataset)
        super().run_fitting()

    def run_fitting(self):
        guess_2 = model.guess(self.S21_2, f=self.frequencies)
        self.fit_frequencies = np.linspace(self.frequencies[0],self.frequencies[-1],400)
        self.fit_result_2 = model.fit(self.S21_2, params=guess_2, f=self.frequencies)
        self.fit_IQ_2 = model.eval(self.fit_result_2.params, f=self.fit_frequencies)

        fit_values_2 = self.fit_result_2.values

        # self.distances_01 = np.abs(self.fit_IQ_1 - self.fit_IQ_0)
        # self.distances_12 = np.abs(self.fit_IQ_2 - self.fit_IQ_1)
        # self.distances_20 = np.abs(self.fit_IQ_0 - self.fit_IQ_2)
        self.distances_01 = np.abs(self.S21_0 - self.S21_1)
        self.distances_12 = np.abs(self.S21_1 - self.S21_2)
        self.distances_20 = np.abs(self.S21_2 - self.S21_0)
        self.total_distance = (self.distances_01 + self.distances_12 + self.distances_20)/3
        self.index_of_max_distance = np.argmax(self.total_distance)
        # self.optimal_frequency = self.fit_frequencies[self.index_of_max_distance]
        self.optimal_frequency = self.frequencies[self.index_of_max_distance]

        return [self.optimal_frequency]

    def plotter(self,ax):
        this_qubit = self.dataset.attrs['qubit']
        ax.set_xlabel('RO frequency')
        ax.set_ylabel('IQ distance')
        ax.plot(self.frequencies, np.abs(self.S21_0),label='0')
        ax.plot(self.frequencies, np.abs(self.S21_1),label='1')
        ax.plot(self.frequencies, np.abs(self.S21_2),label='2')
        ax.plot(self.frequencies, self.total_distance,'--',label='distance')
        # ax.plot(self.frequencies, self.distances_01,label='01')
        # ax.plot(self.frequencies, self.distances_12,label='12')
        # ax.plot(self.frequencies, self.distances_20,label='20')
        # ax.plot(self.fit_frequencies, self.distances_01,label='01')
        # ax.plot(self.fit_frequencies, self.distances_12,label='12')
        # ax.plot(self.fit_frequencies, self.distances_20,label='20')
        # ax.plot(self.fit_frequencies, self.total_distance,label='total')
        optimal_distance = self.total_distance[self.index_of_max_distance]

        ax.scatter(
            self.optimal_frequency, optimal_distance,
            marker='*',c='red', s=64,
        )
        ax.grid()
