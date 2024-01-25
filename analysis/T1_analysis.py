"""
Module containing a class that fits and plots data from a T1 experiment.
"""
import numpy as np
import lmfit
from quantify_core.analysis.fitting_models import ExpDecayModel,fft_freq_phase_guess
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
        self.independents = dataset[coord].values
        self.fit_results = {}
        self.qubit = dataset[data_var].attrs['qubit']

    def run_fitting(self):
        model = ExpDecayModel()

        self.magnitudes = np.absolute(self.S21)
        delays = self.independents

        # Gives an initial guess for the model parameters and then fits the model to the data.
        guess = model.guess(data=self.magnitudes, delay=delays)
        fit_result = model.fit(self.magnitudes, params=guess, t=delays)

        self.fit_delays = np.linspace( delays[0], delays[-1], 400) # x-values for plotting
        self.fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_delays})
        #self.dataset['fit_delays'] = self.fit_delays
        #self.dataset['fit_y'] = ('fit_delays',fit_y)
        T1_time = fit_result.params['tau'].value
        return [T1_time]

    def plotter(self,ax):
        ax.plot( self.fit_delays , self.fit_y,'r-',lw=3.0)
        ax.plot(self.independents, self.magnitudes,'bo-',ms=3.0)
        ax.set_title(f'T1 experiment for {self.qubit}')
        ax.set_xlabel('Delay (s)')
        ax.set_ylabel('|S21| (V)')

        ax.grid()

def cos_func(
    x: float,
    frequency: float,
    amplitude: float,
    offset: float,
    x0: float,
    phase: float = 0,
) -> float:
    return amplitude * np.cos(2 * np.pi * frequency * (x + phase)) * np.exp(-x/x0) + offset

class T2Model(lmfit.model.Model):
    """
    Generate a cosine model that can be fit to Rabi oscillation data.
    """
    def __init__(self, *args, **kwargs):
        # Pass in the defining equation so the user doesn't have to later.
        super().__init__(cos_func, *args, **kwargs)

        # Enforce oscillation frequency is positive
        self.set_param_hint("frequency", min=0)

        # Fix the phase at pi so that the ouput is at a minimum when drive_amp=0
        self.set_param_hint("phase", min = -0.5, max = 0.5)

        # Pi-pulse amplitude can be derived from the oscillation frequency
        self.set_param_hint("duration", expr="1/frequency", vary=False)
        self.set_param_hint("swap", expr="1/(2*frequency)-phase", vary=False)
        self.set_param_hint("cz", expr="2/(2*frequency)-phase", vary=False)


    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        x = kws.get("x", None)
        if x is None:
            return None

        amp_guess = abs(max(data) - min(data)) / 2  # amp is positive by convention
        offs_guess = np.mean(data)

        # Frequency guess is obtained using a fast fourier transform (FFT).
        (freq_guess, _) = fft_freq_phase_guess(data, x)

        self.set_param_hint("x0", value=x[-1]/2, min=0)
        self.set_param_hint("frequency", value=freq_guess, min=0)
        self.set_param_hint("amplitude", value=amp_guess, min=-1.5*amp_guess)
        self.set_param_hint("offset", value=offs_guess)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)

class T2Analysis():
    """
    Analysis that fits an exponential decay function to obtain
    the T2 coherence time from experiment data.
    """
    def  __init__(self,dataset: xr.Dataset):
        data_var = list(dataset.data_vars.keys())[0]
        coord = list(dataset[data_var].coords.keys())[0]
        self.S21 = dataset[data_var].values
        self.independents = dataset[coord].values
        self.fit_results = {}
        self.qubit = dataset[data_var].attrs['qubit']

    def run_fitting(self):
        model = T2Model()

        self.magnitudes = np.absolute(self.S21)
        delays = self.independents

        self.fit_delays = np.linspace( delays[0], delays[-1], 400) # x-values for plotting

        # Gives an initial guess for the model parameters and then fits the model to the data.
        guess = model.guess(data=self.magnitudes, x=delays)
        fit_result = model.fit(self.magnitudes, params=guess, x=delays)

        self.fit_delays = np.linspace( delays[0], delays[-1], 400)
        self.fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_delays})
        #self.dataset['fit_delays'] = self.fit_delays
        #self.dataset['fit_y'] = ('fit_delays',fit_y)
        self.T2_time = fit_result.params['x0'].value
        return [self.T2_time]

    def plotter(self,ax):
        ax.plot(self.fit_delays , self.fit_y,'r-',lw=3.0)
        ax.plot(self.independents, self.magnitudes,'bo-',ms=3.0)
        ax.set_title(f'T2 experiment for {self.qubit}')
        ax.set_xlabel('Delay (s)')
        ax.set_ylabel('|S21| (V)')

        ax.grid()

class T2EchoAnalysis():
    """
    Analysis that fits an exponential decay function to obtain
    the T1 relaxation time from experiment data.
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

        self.magnitudes = np.absolute(self.S21)
        delays = self.independents

        self.fit_delays = np.linspace( delays[0], delays[-1], 400) # x-values for plotting

        # Gives an initial guess for the model parameters and then fits the model to the data.
        guess = model.guess(data=self.magnitudes, delay=delays)
        fit_result = model.fit(self.magnitudes, params=guess, t=delays)

        self.fit_delays = np.linspace( delays[0], delays[-1], 400)
        self.fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_delays})
        #self.dataset['fit_delays'] = self.fit_delays
        #self.dataset['fit_y'] = ('fit_delays',fit_y)
        self.T2_Echo_time = fit_result.params['tau'].value
        return [self.T2_Echo_time]

    def plotter(self,ax):
        ax.plot( self.fit_delays , self.fit_y,'r-',lw=3.0)
        ax.plot(self.independents, self.magnitudes,'bo-',ms=3.0)
        ax.set_title(f'T2 Echo experiment for {self.qubit}')
        ax.set_xlabel('Delay (s)')
        ax.set_ylabel('|S21| (V)')

        ax.grid()
