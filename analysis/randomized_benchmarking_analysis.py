"""
Module containing classes that model, fit and plot data from a Rabi experiment.
"""
import numpy as np
import lmfit
from quantify_core.analysis.fitting_models import ExpDecayModel
import xarray as xr


class RandomizedBenchmarkingAnalysis():
    """
    Analysis that fits an exponential decay function to randomized benchmarking data.
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
        model = ExpDecayModel()

        self.magnitudes = np.abs(self.S21)
        n_cliffords = self.independents

        # Gives an initial guess for the model parameters and then fits the model to the data.
        #guess = model.guess(data=self.magnitudes, delay=delays)
        #fit_result = model.fit(self.magnitudes, params=guess, t=delays)

        self.fit_n_cliffords = np.linspace( n_cliffords[0], n_cliffords[-1], 400)
        #self.fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_delays})

        #print(f'{ self.magnitudes = }')
        return [0]

    def plotter(self,ax):
        # Plots the data and the fitted model of a Rabi experiment
        #ax.plot( self.fit_amplitudes , self.fit_y,'r-',lw=3.0, label=f" π_ampl = {self.ampl:.2E} ± {self.uncertainty:.1E} (V)")
        ax.plot( self.independents, self.magnitudes,'bo-',ms=3.0)
        ax.set_title(f'Randomized benchmarking for {self.qubit}')
        ax.set_xlabel('Number of clifford operations')
        ax.set_ylabel('|S21| (V)')
        ax.grid()

