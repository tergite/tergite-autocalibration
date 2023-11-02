import numpy as np
import xarray as xr
from analysis.qubit_spectroscopy_analysis import QubitSpectroscopyAnalysis


class CouplerSpectroscopyAnalysis():
    def __init__(self, dataset: xr.Dataset):
        data_var = list(dataset.data_vars.keys())[0]
        self.qubit = dataset[data_var].attrs['qubit']
        self.S21 = dataset[data_var].values
        for coord in dataset[data_var].coords:
            if 'frequencies' in coord:
                self.frequencies = coord
            elif 'currents' in coord:
                self.currents = coord
        # dataset[f'y{self.qubit}'].values = np.abs(self.S21)
        self.data_var = data_var
        self.dataset = dataset

    def run_fitting(self):
        self.dc_currents = self.dataset[f'y{self.qubit}'][self.currents]
        self.qubit_frequencies = []
        for i, current in enumerate(self.dc_currents.values):
            partial_ds = self.dataset[f'y{self.qubit}'].isel({self.currents: [i]})[0]
            analysis = QubitSpectroscopyAnalysis(partial_ds.to_dataset())
            qubit_frequency = analysis.run_fitting()

            self.qubit_frequencies.append(qubit_frequency)
        #TODO Qutip Analysis
        return 0

    def plotter(self,ax):
        self.dataset[self.data_var].plot(ax=ax, x=self.frequencies)
        ax.scatter(self.qubit_frequencies, self.dc_currents, s=64, c='red')
