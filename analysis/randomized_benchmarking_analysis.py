"""
Module containing classes that model, fit and plot data from a Rabi experiment.
"""
import numpy as np
import lmfit
from quantify_core.analysis.fitting_models import fft_freq_phase_guess
import xarray as xr


class RandomizedBenchmarkingAnalysis():
    """
    Analysis that fits a cosine function to Rabi oscillation data.
    """
    def  __init__(self,dataset: xr.Dataset):
        data_var = list(dataset.data_vars.keys())[0]
        coord = list(dataset[data_var].coords.keys())[0]
        self.S21 = dataset[data_var].values
        self.independents = dataset[coord].values
        self.fit_results = {}
        self.qubit = dataset[data_var].attrs['qubit']

    def run_fitting(self):
        #TODO
        return []

    def plotter(self,ax):
        # Plots the data and the fitted model of a Rabi experiment
        ax.plot( self.fit_amplitudes , self.fit_y,'r-',lw=3.0, label=f" π_ampl = {self.ampl:.2E} ± {self.uncertainty:.1E} (V)")
        ax.plot( self.independents, self.magnitudes,'bo-',ms=3.0)
        ax.set_title(f'Rabi Oscillations for {self.qubit}')
        ax.set_xlabel('Amplitude (V)')
        ax.set_ylabel('|S21| (V)')
        ax.grid()

