import numpy as np
import lmfit
from quantify_core.analysis.fitting_models import fft_freq_phase_guess
import xarray as xr

def cos_func(
    drive_amp: float,
    frequency: float,
    amplitude: float,
    offset: float,
    phase: float = 0,
) -> float:
    return amplitude * np.cos(2 * np.pi * frequency * drive_amp + phase) + offset


class RabiModel(lmfit.model.Model):
    def __init__(self, *args, **kwargs):
        # pass in the defining equation so the user doesn't have to later.
        super().__init__(cos_func, *args, **kwargs)

        # Enforce oscillation frequency is positive
        self.set_param_hint("frequency", min=0)

        # Fix the phase at pi so that the ouput is at a minimum when drive_amp=0
        self.set_param_hint("phase", expr="3.141592653589793", vary=False)

        # Pi-pulse amplitude can be derived from the oscillation frequency
        self.set_param_hint("amp180", expr="1/(2*frequency)", vary=False)


    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        drive_amp = kws.get("drive_amp", None)
        if drive_amp is None:
            return None

        amp_guess = abs(max(data) - min(data)) / 2  # amp is positive by convention
        offs_guess = np.mean(data)

        (freq_guess, _) = fft_freq_phase_guess(data, drive_amp)

        self.set_param_hint("frequency", value=freq_guess, min=0)
        self.set_param_hint("amplitude", value=amp_guess, min=0)
        self.set_param_hint("offset", value=offs_guess)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)

class RabiAnalysis():
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

    def run_fitting(self):
        model = RabiModel()
        self.magnitudes = np.absolute(self.S21)
        amplitudes = self.independents
        self.fit_amplitudes = np.linspace( amplitudes[0], amplitudes[-1], 400)

        guess = model.guess(self.magnitudes, drive_amp=amplitudes)
        # print(f'{ guess = }')
        fit_result = model.fit(self.magnitudes, params=guess, drive_amp=amplitudes)

        self.fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_amplitudes})
        return fit_result.params['amp180'].value

    def plotter(self,ax):
        ax.plot( self.fit_amplitudes , self.fit_y,'r-',lw=3.0)
        ax.plot( self.independents, self.magnitudes,'bo-',ms=3.0)
        ax.set_title(f'Rabi Oscillations for {self.qubit}')
        ax.set_xlabel('Amplitude (V)')
        ax.set_ylabel('|S21| (V)')
        ax.grid()

