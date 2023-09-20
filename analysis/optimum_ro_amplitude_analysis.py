"""
Module containing a class that fits data from a resonator spectroscopy experiment.
"""
import numpy as np
from quantify_core.analysis import fitting_models as fm
import redis
import xarray as xr
redis_connection = redis.Redis(decode_responses=True)

class OptimalROAmplitudeAnalysis():
    """
    Analysis that  extracts the optimal RO amplitude.
    """
    def __init__(self, dataset: xr.Dataset):
        self.dataset = dataset
        data_var = list(dataset.data_vars.keys())[0]
        self.S21_0 = dataset[data_var][0].values
        self.S21_1 = dataset[data_var][1].values

        for coord in dataset.coords:
            if 'amplitudes' in str(coord):
                self.amplitudes = dataset[coord].values

        self.fit_results = {}

    def run_fitting(self):
        self.optimal_amplitude = 0
        return self.optimal_amplitude

    def plotter(self,ax):
        # this_qubit = self.dataset.attrs['qubit']
        # ax.set_xlabel('I quadrature (V)')
        # ax.set_ylabel('Q quadrature (V)')
        # ax.plot(self.fit_IQ_0.real, self.fit_IQ_0.imag)
        # ax.plot(self.fit_IQ_1.real, self.fit_IQ_1.imag)
        # f0 = self.fit_IQ_0[self.index_of_max_distance]
        # f1 = self.fit_IQ_1[self.index_of_max_distance]
        #
        # ro_freq = float(redis_connection.hget(f'transmons:{this_qubit}', 'ro_freq'))
        # ro_freq_1 = float(redis_connection.hget(f'transmons:{this_qubit}', 'ro_freq_1'))
        #
        # label_text = f'opt_ro: {int(self.optimal_frequency)}\n|0>_ro: {int(ro_freq)}\n|1>_ro: {int(ro_freq_1)}' 
        #
        # ax.scatter(
        #     [f0.real, f1.real], [f0.imag, f1.imag], 
        #     marker='*',c='red', s=64,  label=label_text
        # )
        ax.grid()
