import numpy as np
import xarray as xr

from tergite_autocalibration.lib.analysis_base import BaseAnalysis


class MotzoiAnalysis(BaseAnalysis):
    def __init__(self, dataset: xr.Dataset):
        super().__init__()
        data_var = list(dataset.data_vars.keys())[0]
        coord = list(dataset[data_var].coords.keys())[0]
        self.S21 = dataset[data_var].values
        self.independents = dataset[coord].values
        self.fit_results = {}
        self.qubit = dataset[data_var].attrs['qubit']
        # print(data_var)
        dataset[f'y{self.qubit}'].values = np.abs(self.S21)
        # dataset[data_var].values = np.abs(self.S21)
        self.dataset = dataset

    def run_fitting(self):
        motzoi_key = 'mw_motzois' + self.qubit
        motzois = self.dataset[motzoi_key].size
        sums = []
        for this_motzoi_index in range(motzois):
            this_sum = sum(np.abs(self.dataset[f'y{self.qubit}'][this_motzoi_index].values))
            sums.append(this_sum)

        index_of_min = np.argmin(np.array(sums))
        self.optimal_motzoi = float(self.dataset[motzoi_key][index_of_min].values)

        return [self.optimal_motzoi]

    def plotter(self, axis):
        datarray = self.dataset[f'y{self.qubit}']
        qubit = self.qubit

        datarray.plot(ax=axis, x=f'mw_motzois{qubit}', cmap='RdBu_r')
        axis.axvline(self.optimal_motzoi, c='k', lw=4, linestyle='--')
