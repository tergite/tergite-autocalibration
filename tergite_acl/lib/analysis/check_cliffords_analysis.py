"""
Module containing classes that model, fit and plot data from a Rabi experiment.
"""
import numpy as np
import xarray as xr


class CheckCliffordsAnalysis():
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

        self.theoretical_magnitudes = [0,1,1,1,1,0,1,0,1,0,
                                       0,0,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,
                                       0.5,0.5,0.5,0.5]
        

    def run_fitting(self):
        self.magnitudes = np.abs(self.S21)
        self.independents

        self.normalized_magnitudes = (self.magnitudes-self.magnitudes[0])/(self.magnitudes[1]-self.magnitudes[0])
        return [0]

    def plotter(self,ax):        
        # unnormalized plot:
        ax.plot( self.independents[:-2], self.theoretical_magnitudes,'ro',lw=3.0, label=f"Theoretical clifford magnitudes")
        ax.plot( self.independents[:-2], self.normalized_magnitudes[2:],'bo',ms=3.0, label=f"Measured clifford magnitudes")
        ax.hlines(y=self.magnitudes[0],xmin=self.independents[0],xmax=self.independents[-1],color='g',linestyle='--') # Plots |0⟩
        ax.hlines(y=self.magnitudes[1],xmin=self.independents[0],xmax=self.independents[-1],color='g',linestyle='--') # Plots |1⟩
        ax.set_ylabel(f'|S21| (V)')
        ax.set_title(f'Clifford check for {self.qubit}')
        ax.set_xlabel('Clifford gate index') #from utils/clifford_elements_decomposition.py
        ax.grid()

