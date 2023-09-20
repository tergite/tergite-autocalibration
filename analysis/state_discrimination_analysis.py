"""
Module containing classes that model, fit and plot data from a Rabi experiment.
"""
import numpy as np
import lmfit
import xarray as xr

class StateDiscrimination():
    """
    Analysis that fits a cosine function to Rabi oscillation data.
    """
    def  __init__(self,dataset: xr.Dataset):
        data_var = list(dataset.data_vars.keys())[0]
        coord = list(dataset[data_var].coords.keys())[0]
        self.S21 = dataset[data_var].values
        self.I = self.S21.real
        self.Q = self.S21.imag
        self.independents = dataset[coord].values
        self.fit_results = {}
        self.qubit = dataset[data_var].attrs['qubit']

    def run_fitting(self):
        pass

        # #Initialize the Rabi model
        # model = RabiModel()
        # #Fetch the resulting measurement variables from self
        # self.magnitudes = np.absolute(self.S21)
        # amplitudes = self.independents
        # self.fit_amplitudes = np.linspace( amplitudes[0], amplitudes[-1], 400) # x-values for plotting
        # # Gives an initial guess for the model parameters and then fits the model to the data.
        # guess = model.guess(self.magnitudes, drive_amp=amplitudes)
        # fit_result = model.fit(self.magnitudes, params=guess, drive_amp=amplitudes)
        # self.fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_amplitudes})
        # return fit_result.params['amp180'].value

    def plotter(self,ax):
        # Plots the data and the fitted model of a Rabi experiment
        ax.scatter( self.I , self.Q, size=36)
        ax.set_title(f'State Discrimination for {self.qubit}')
        ax.set_xlabel('I (V)')
        ax.set_ylabel('Q (V)')
        ax.grid()
