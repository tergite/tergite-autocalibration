import numpy as np
import xarray as xr

class PunchoutAnalysis():
    def  __init__(self,dataset: xr.Dataset):
        data_var = list(dataset.data_vars.keys())[0]
        coord = list(dataset[data_var].coords.keys())[0]
        self.S21 = dataset[data_var].values
        self.independents = dataset[coord].values
        self.fit_results = {}
        self.qubit = dataset[data_var].attrs['qubit']
        dataset[f'y{self.qubit}'].values = np.abs(self.S21)
        self.dataset = dataset

    def run_fitting(self):
        # motzoi_key = 'mw_motzois'+self.qubit
        # motzois = self.dataset[motzoi_key].size
        # sums = []
        # for this_motzoi_index in range(motzois):
        #     this_sum = sum(np.abs(self.dataset[f'y{self.qubit}'][this_motzoi_index].values))
        #     sums.append(this_sum)
        #
        # index_of_min = np.argmin(np.array(sums))
        # self.optimal_motzoi = float(self.dataset[motzoi_key][index_of_min].values)

        pass

    def plotter(self,axis):
        datarray = self.dataset[f'y{self.qubit}']
        qubit = self.qubit

        datarray.plot()

