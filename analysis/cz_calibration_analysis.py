import numpy as np
import xarray as xr
from utilities.redis_helper import fetch_redis_params

class CZCalibrationAnalysis():
    def  __init__(self,dataset: xr.Dataset):
        data_var = list(dataset.data_vars.keys())[0]
        coord = list(dataset[data_var].coords.keys())[0]
        self.S21 = dataset[data_var].values
        self.independents = dataset[coord].values
        self.fit_results = {}
        self.qubit = dataset[data_var].attrs['qubit']
        dataset[f'y{self.qubit}_'].values = np.abs(self.S21)
        self.dataset = dataset

    def run_fitting(self):
        ramsey_phases_key = 'ramsey_phases'+self.qubit
        ramsey_phases = self.dataset[ramsey_phases_key].size
        # for this_frequency_index in range(frequencies):
        #     freqs = self.dataset[f'y{self.qubit}_'][this_frequency_index].values
        #     amps = self.dataset[amplitude_key].values

        return 0

    def plotter(self,axis):
        datarray = self.dataset[f'y{self.qubit}_']
        qubit = self.qubit
        datarray.plot(ax=axis, x=f'ramsey_phases{qubit}')
        # axis.axvline(self.optimal_motzoi-fetch_redis_params('mw_amp180',self.qubit), c='red', lw=4)
