import lmfit
from matplotlib.pyplot import plot
import numpy as np
import xarray as xr
from quantify_core.analysis.fitting_models import fft_freq_phase_guess

from tergite_acl.lib.analysis_base import BaseAnalysis


class All_XY_Analysis(BaseAnalysis):

    def __init__(self, dataset: xr.Dataset):
        super().__init__()
        data_var = list(dataset.data_vars.keys())[0]
        coord = list(dataset[data_var].coords.keys())[0]
        self.S21 = dataset[data_var].values
        self.independents = dataset[coord].values
        self.calibration_0 = self.S21[-2]
        self.calibration_1 = self.S21[-1]
        self.magnitudes = np.absolute(self.S21[:-2])
        self.fit_results = {}
        self.qubit = dataset[data_var].attrs['qubit']

    def run_fitting(self):
        self.rotated_data = self.rotate_to_probability_axis(self.S21)

        return [0]

    def plotter(self, ax):
        ax.set_title(f'All-XY analysis_base for {self.qubit}')
        ax.scatter(self.independents[:-2], self.rotated_data, marker='o', s=48)
        ax.set_xlabel('Gate')
        ax.set_ylabel('|S21| (V)')
        ax.grid()
