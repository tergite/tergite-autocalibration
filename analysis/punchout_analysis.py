import numpy as np
import xarray as xr

class PunchoutAnalysis():
    def  __init__(self,dataset: xr.Dataset):
        data_var = list(dataset.data_vars.keys())[0]
        self.qubit = dataset[data_var].attrs['qubit']
        self.S21 = dataset[data_var].values
        for coord in dataset[data_var].coords:
            if 'frequencies' in coord: self.frequencies = coord
            elif 'amplitudes' in coord: self.amplitudes = coord
        dataset[f'y{self.qubit}'].values = np.abs(self.S21)
        self.data_var = data_var
        self.dataset = dataset

    def run_fitting(self):
        magnitudes = self.dataset[f'y{self.qubit}'].values
        norm_magnitudes = magnitudes /np.max(magnitudes, axis=0)
        self.dataset[f'y{self.qubit}'].values = norm_magnitudes

        # motzoi_key = 'mw_motzois'+self.qubit
        # motzois = self.dataset[motzoi_key].size
        # sums = []
        # for this_motzoi_index in range(motzois):
        #     this_sum = sum(np.abs(self.dataset[f'y{self.qubit}'][this_motzoi_index].values))
        #     sums.append(this_sum)
        #
        # index_of_min = np.argmin(np.array(sums))
        # self.optimal_motzoi = float(self.dataset[motzoi_key][index_of_min].values)
        return [0]

    def plotter(self,ax):
        datarray = self.dataset[f'y{self.qubit}']
        qubit = self.qubit
        self.dataset[self.data_var].plot(ax=ax, x=self.frequencies, yscale='log')
