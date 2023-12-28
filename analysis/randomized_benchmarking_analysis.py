"""
Module containing classes that model, fit and plot data from a Rabi experiment.
"""
import numpy as np
import lmfit
from quantify_core.analysis.fitting_models import ExpDecayModel
import xarray as xr

def exponential_decay_function( x: float, amplitude: float, B: float, offset: float) -> float:
    return amplitude*np.exp(-x/B) + offset


class ExpDecayModel(lmfit.model.Model):
    """
    Generate an exponential decay model that can be fit to randomized benchmarking data.
    """
    def __init__(self, *args, **kwargs):

        super().__init__(exponential_decay_function, *args, **kwargs)

        self.set_param_hint("amplitude", vary=True)
        self.set_param_hint("B", vary=True, min=0)
        self.set_param_hint("offset", vary=True)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        x = kws.get("x", None)

        if x is None:
            return None
        
        amplitude_guess= data[0]-data[-1]
        self.set_param_hint("amplitude", value=amplitude_guess)

        offset_guess = data[-1]
        self.set_param_hint("offset", value=offset_guess)

        B_guess = (x[-1]+x[0])/2
        self.set_param_hint("B", value=B_guess)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)



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
        model = ExpDecayModel()

        self.magnitudes = np.abs(self.S21)
        n_cliffords = self.independents

        # Gives an initial guess for the model parameters and then fits the model to the data.
        guess = model.guess(data=self.magnitudes, x=n_cliffords)
        #print(f'{ guess= }')
        fit_result = model.fit(self.magnitudes, params=guess, x=n_cliffords)
        
        self.fit_n_cliffords = np.linspace( n_cliffords[0], n_cliffords[-1], 400)
        self.fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_n_cliffords})
        #print(f'{ fit_result.params= }')
        
        return [0]

    def plotter(self,ax):
        # Plots the data and the fitted model of a Rabi experiment
        ax.plot( self.fit_n_cliffords , self.fit_y,'r-',lw=3.0)#, label=f" π_ampl = {self.ampl:.2E} ± {self.uncertainty:.1E} (V)")
        ax.plot( self.independents, self.magnitudes,'bo-',ms=3.0)
        ax.set_title(f'Randomized benchmarking for {self.qubit}')
        ax.set_xlabel('Number of clifford operations')
        ax.set_ylabel('|S21| (V)')
        ax.grid()

