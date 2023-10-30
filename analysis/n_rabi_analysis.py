import numpy as np
import xarray as xr
from utilities.redis_helper import fetch_redis_params

class NRabiAnalysis():
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
        motzoi_key = 'mw_amplitudes_sweep'+self.qubit
        motzois = self.dataset[motzoi_key].size
        sums = []
        for this_motzoi_index in range(motzois):
            this_sum = sum(np.abs(self.dataset[f'y{self.qubit}_'][this_motzoi_index].values))
            sums.append(this_sum)

        index_of_min = np.argmax(np.array(sums))
        self.optimal_motzoi = float(self.dataset[motzoi_key][index_of_min].values)+fetch_redis_params('mw_amp180',self.qubit)

        return self.optimal_motzoi

    def plotter(self,axis):
        datarray = self.dataset[f'y{self.qubit}_']
        qubit = self.qubit


        datarray.plot(ax=axis, x=f'mw_amplitudes_sweep{qubit}')
        axis.axvline(self.optimal_motzoi-fetch_redis_params('mw_amp180',self.qubit), c='red', lw=4)
