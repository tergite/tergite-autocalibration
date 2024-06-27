import numpy as np
import xarray as xr

from tergite_autocalibration.lib.analysis_base import BaseAnalysis
from tergite_autocalibration.utils.redis_utils import fetch_redis_params


class NRabiAnalysis(BaseAnalysis):
    def  __init__(self, dataset: xr.Dataset):
        super().__init__()
        self.data_var = list(dataset.data_vars.keys())[0]
        for coord in dataset[self.data_var].coords:
            if 'amplitudes' in coord:
                self.mw_amplitudes_coord = coord
            elif 'repetitions' in coord:
                self.X_repetitions = coord
        self.S21 = dataset[self.data_var].values
        self.independents = dataset[coord].values
        self.fit_results = {}
        self.qubit = dataset[self.data_var].attrs['qubit']
        dataset[f'y{self.qubit}'].values = np.abs(self.S21)
        self.dataset = dataset

    def run_fitting(self):
        mw_amplitude_key = self.mw_amplitudes_coord
        # mw_amplitude_key = 'mw_amplitudes_sweep' + self.qubit
        mw_amplitudes = self.dataset[mw_amplitude_key].size
        sums = []
        for this_amplitude_index in range(mw_amplitudes):
            this_sum = sum(np.abs(self.dataset[f'y{self.qubit}'][this_amplitude_index].values))
            sums.append(this_sum)

        index_of_max = np.argmax(np.array(sums))
        self.previous_amplitude = fetch_redis_params('rxy:amp180',self.qubit)
        self.optimal_amp180 = self.dataset[mw_amplitude_key][index_of_max].values + self.previous_amplitude
        self.index_of_max = index_of_max

        return [self.optimal_amp180]

    def plotter(self, axis):
        datarray = self.dataset[f'y{self.qubit}']
        qubit = self.qubit

        datarray.plot(ax=axis, x=f'mw_amplitudes_sweep{qubit}',cmap='RdBu_r')
        axis.set_xlabel('mw amplitude correction')
        axis.axvline(
            # self.dataset[self.mw_amplitudes_coord][self.index_of_max].values,
            self.optimal_amp180 - fetch_redis_params('rxy:amp180',self.qubit),
            c='k',
            lw=4,
            linestyle ='--'
        )
