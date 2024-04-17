import lmfit
import numpy as np
import xarray as xr
from quantify_core.analysis.fitting_models import fft_freq_phase_guess

from tergite_acl.lib.analysis_base import BaseAnalysis


class All_XY_Analysis(BaseAnalysis):
    """
    Analysis that fits a cosine function to Rabi oscillation data.
    """

    def __init__(self, dataset: xr.Dataset):
        super().__init__()
        data_var = list(dataset.data_vars.keys())[0]
        coord = list(dataset[data_var].coords.keys())[0]
        self.S21 = dataset[data_var].values
        self.independents = dataset[coord].values
        self.fit_results = {}
        self.qubit = dataset[data_var].attrs['qubit']

    def run_fitting(self):
        # Initialize the Rabi model

        return []

    def plotter(self, ax):
        # Plots the data and the fitted model of a Rabi experiment
        # ax.set_title(f'Rabi Oscillations for {self.qubit}')
        # ax.set_xlabel('Amplitude (V)')
        # ax.set_ylabel('|S21| (V)')
        ax.grid()
