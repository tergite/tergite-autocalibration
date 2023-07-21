import numpy as np
from quantify_core.analysis import fitting_models as fm
import xarray as xr
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
colorama_init()

model = fm.ResonatorModel()

class ResonatorSpectroscopyAnalysis():
    def __init__(self, dataset: xr.Dataset):
        data_var = list(dataset.data_vars.keys())[0]
        print('data_var', data_var)
        coord = list(dataset[data_var].coords.keys())[0]

        self.S21 = dataset[data_var].values
        #######################
        print( "")
        print( f'{Fore.RED}WARNING MOCK DATA IN analysis/resonator_spectroscopy_analysis{Style.RESET_ALL}')
        self.S21 = np.array([1+1j for _ in self.S21])
        #######################
        self.frequencies = dataset[coord].values
        self.fit_results = {}

    def run_fitting(self):
        S21 = self.S21
        frequencies = self.frequencies
        guess = model.guess(S21, f=frequencies)

        fit_result = model.fit(S21, params=guess, f=frequencies)

        self.fit_results.update({"hanger_func_complex_SI": fit_result})
