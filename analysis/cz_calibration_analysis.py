import numpy as np
import xarray as xr
from utilities.redis_helper import fetch_redis_params
import lmfit
from quantify_core.analysis.fitting_models import fft_freq_phase_guess
from utilities.QPU_connections_visualization import edge_group
import matplotlib.pyplot as plt


# Cosine function that is fit to Rabi oscillations
def cos_func(
    drive_amp: float,
    frequency: float,
    amplitude: float,
    offset: float,
    phase: float = 0,
) -> float:
    return amplitude * np.cos(2 * np.pi * frequency * (drive_amp + phase)) + offset

class CZModel(lmfit.model.Model):
    """
    Generate a cosine model that can be fit to Rabi oscillation data.
    """
    def __init__(self, *args, **kwargs):
        # Pass in the defining equation so the user doesn't have to later.
        super().__init__(cos_func, *args, **kwargs)

        # Enforce oscillation frequency is positive
        self.set_param_hint("frequency", min=0)

        # Fix the phase at pi so that the ouput is at a minimum when drive_amp=0
        self.set_param_hint("phase", min = 0, max = 360)

        # Pi-pulse amplitude can be derived from the oscillation frequency

        # self.set_param_hint("swap", expr="1/(2*frequency)-phase", vary=False)
        self.set_param_hint("cz", expr="2/(2*frequency)-phase", vary=False)


    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        drive_amp = kws.get("drive_amp", None)
        if drive_amp is None:
            return None

        amp_guess = abs(max(data) - min(data)) / 2  # amp is positive by convention
        offs_guess = np.mean(data)

        # Frequency guess is obtained using a fast fourier transform (FFT).
        (freq_guess, _) = fft_freq_phase_guess(data, drive_amp)

        self.set_param_hint("frequency", value=freq_guess, min=0)
        self.set_param_hint("amplitude", value=amp_guess, min=0)
        self.set_param_hint("offset", value=offs_guess)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)

class CZCalibrationAnalysis():
    def  __init__(self,dataset: xr.Dataset):
        data_var = list(dataset.data_vars.keys())[0]
        coord = list(dataset[data_var].coords.keys())[0]
        self.S21 = dataset[data_var].values
        self.independents = dataset[coord].values
        self.fit_results = {}
        self.qubit = dataset[data_var].attrs['qubit']
        dataset[f'y{self.qubit}'].values = np.abs(self.S21)
        self.dataset = dataset

    def run_fitting(self):
        # self.testing_group = 0
        self.dynamic = self.dataset['name']  == 'cz_dynamic_phase'
        self.freq = self.dataset[f'control_ons{self.qubit}'].values
        self.amp = self.dataset[f'ramsey_phases{self.qubit}'].values
        magnitudes = self.dataset[f'y{self.qubit}'].values
        self.magnitudes = np.transpose(magnitudes)
        # self.magnitudes = np.transpose((magnitudes - np.min(magnitudes))/(np.max(magnitudes)-np.min(magnitudes)))
        self.fit_amplitudes = np.linspace( self.amp[0], self.amp[-1], 400)

        self.fit_results,self.fit_ys = [],[]
        for magnitude in self.magnitudes:
            if int(self.qubit[1:]) % 2 == 0:
                fit = True
                model = CZModel()
                # magnitude = np.transpose(values)[15]
                guess = model.guess(magnitude, drive_amp=self.amp)
                fit_result = model.fit(magnitude, params=guess, drive_amp=self.amp)
                fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_amplitudes})
                self.fit_results.append(fit_result)
                self.qubit_type = 'Target'
            else:
                fit = False
                fit_y = [np.mean(magnitude)]*400
                self.qubit_type = 'Control'
            self.fit_ys.append(fit_y)
        if fit:
            qois = np.transpose([[[fit.result.params[p].value,fit.result.params[p].stderr] for p in ['cz']] for fit in self.fit_results])
            opt_cz = qois[0][0]
            self.cphase = 180-np.abs(np.abs(np.diff(opt_cz))[0]-180)
            self.err = np.sqrt(np.sum(np.array(qois[1][0])**2))
        else:
            self.cphase = 0
            self.err = 0
            self.opt_cz = [0]*2
        return [self.cphase]

    def plotter(self,axis):
        # datarray = self.dataset[f'y{self.qubit}']
        # qubit = self.qubit

        if self.dynamic:
            label = ['Gate Off','Gate On']
            name = 'Dynamic Phase'
        else:
            label = ['Control Off','Control On']
            name = 'CZ'
        x = range(len(label))
        colors = plt.get_cmap('RdBu_r')(np.linspace(0.2, 0.8, len(x)))

        for index,magnitude in enumerate(self.magnitudes):
            axis.plot(self.amp,magnitude,'.',c = colors[index])
            axis.plot(self.fit_amplitudes,self.fit_ys[index],'-',c = colors[index],label = label[index])
            axis.vlines(self.opt_cz[index],-10,10,colors='gray',linestyles='--',linewidth=1.5)

        axis.vlines(0,-10,-10,colors='gray',linestyles='--', label = '{:} = {:.1f}+/-{:.1f}'.format(name,self.cphase,self.err),zorder=-10)
        # axis.legend(loc = 'upper right')
        axis.set_xlim([self.amp[0],self.amp[-1]])
        axis.set_ylim(np.min(self.magnitudes),np.max(self.magnitudes))
        axis.set_xlabel('Phase (deg)')
        axis.set_ylabel('Signal (a.u.)')
        axis.set_title(f'{name} Calibration - {self.qubit_type} Qubit {self.qubit[1:]}')
