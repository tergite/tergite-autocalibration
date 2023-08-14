"""
Module containing a class that fits and plots data from a T1 experiment.
"""
import numpy as np
import lmfit
from quantify_core.analysis.fitting_models import ExpDecayModel
import xarray as xr

class T1Analysis():
    """
    Analysis that fits an exponential decay function to obtain
    the T1 relaxation time from experiment data.
    """
    def  __init__(self,dataset: xr.Dataset):
        data_var = list(dataset.data_vars.keys())[0]
        coord = list(dataset[data_var].coords.keys())[0]
        self.S21 = dataset[data_var].values
        ########################
        #print( "")
        #print( f'{Fore.RED}WARNING MOCK DATA IN analysis/qubit_spectroscopy_analysis{Style.RESET_ALL}')
        #self.S21 = np.array([1+1j for _ in self.S21])
        ########################
        self.independents = dataset[coord].values
        self.fit_results = {}
        self.qubit = dataset[data_var].attrs['qubit']

    def model_fit(self):
        #Initialize the T1 exponential decay model
        model = ExpDecayModel()
        
        #Fetch the resulting measurement variables from self
        self.magnitudes = np.absolute(self.S21)
        delays = self.independents

        self.fit_delays = np.linspace( delays[0], delays[-1], 400) # x-values for plotting

        # Gives an initial guess for the model parameters and then fits the model to the data.
        guess = model.guess(data=self.magnitudes, delay=delays)
        fit_result = model.fit(self.magnitudes, params=guess, t=delays)
        
        self.fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_delays})
        return fit_result.params['tau'].value

    def plotter(self,ax):
    	# Plots the data and the fitted model of a T1 experiment
        ax.plot( self.fit_delays , self.fit_y,'r-',lw=3.0)
        ax.plot(self.independents, self.magnitudes,'bo-',ms=3.0)
        ax.set_title(f'T1 experiment for {self.qubit}')
        ax.set_xlabel('Delay (s)')
        ax.set_ylabel('|S21| (V)')
        ax.grid()
 