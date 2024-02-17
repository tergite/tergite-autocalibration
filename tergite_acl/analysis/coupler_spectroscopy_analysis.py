import matplotlib.pyplot as plt
import numpy as np
from numpy.polynomial.polynomial import Polynomial
import xarray as xr
from tergite_acl.analysis.qubit_spectroscopy_analysis import QubitSpectroscopyAnalysis


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
        dataset[f'y{self.qubit}'].values = np.abs(self.S21)
        self.data_var = data_var
        self.dataset = dataset

    def reject_outliers(self, data, m = 4):
        d = np.abs(data - np.median(data))
        mdev = np.median(d)
        s = d/mdev if mdev else np.zeros(len(d))
        return np.array(s>m)

    def run_fitting(self):
        self.dc_currents = self.dataset[f'y{self.qubit}'][self.currents]
        self.detected_frequencies = []
        self.detected_currents = []
        for i, current in enumerate(self.dc_currents.values):
            partial_ds = self.dataset[f'y{self.qubit}'].isel({self.currents: [i]})[0]
            analysis = QubitSpectroscopyAnalysis(partial_ds.to_dataset())
            qubit_frequency = analysis.run_fitting()[0]
            if not np.isnan(qubit_frequency):
                self.detected_frequencies.append(qubit_frequency)
                self.detected_currents.append(current)

        distances = np.abs(np.gradient(self.detected_frequencies))
        # the reject_outliers array has True at gradient discontinuities
        array_splits = self.reject_outliers(distances).nonzero()[0] + 1
        frequency_splits = np.split(self.detected_frequencies, array_splits)
        currents_splits = np.split(self.detected_currents, array_splits)
        split_data = zip(currents_splits, frequency_splits)
        roots = []
        root_frequencies = []
        for split_currents, split_frequencies in split_data:
            if len(split_frequencies) > 4:
                coupler_fit = Polynomial.fit(split_currents, split_frequencies, 4)
                # fit_currents = np.linspace(split_currents[0], split_currents[-1], 100)
                root = np.mean(np.real(coupler_fit.roots()))
                roots.append(root)
                root_frequencies.append(coupler_fit(root))
        if len(roots) == 0:
            print('No Roots Found, returning zero current')
            return [0]
        I0 = roots[np.argmin(np.abs(roots))]
        I1 = roots[np.argmax(np.abs(roots))]
        DeltaI = I1 - I0
        possible_I = np.array([0.4 * DeltaI + I0, 0.4 * DeltaI - I0])
        self.parking_I = possible_I[np.argmin(np.abs(possible_I))]
        self.roots = roots
        self.root_frequencies = root_frequencies
        return [self.parking_I]

    def plotter(self,ax: plt.Axes):
        self.dataset[self.data_var].plot(ax=ax, x=self.frequencies)
        ax.scatter(self.detected_frequencies, self.detected_currents, s=52, c='red')
        if hasattr(self, 'root_frequencies'):
            ax.scatter(self.root_frequencies, self.roots, s=64, c='black', label=r'$\Phi_0$')
        if hasattr(self, 'parking_I'):
            ax.axhline(self.parking_I, lw=5, ls='dashed',  c='orange', label=f'parking current = {self.parking_I}')
