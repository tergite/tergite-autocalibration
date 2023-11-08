import numpy as np
import xarray as xr
from utilities.redis_helper import fetch_redis_params
import lmfit
from quantify_core.analysis.fitting_models import fft_freq_phase_guess
from utilities.QPU_connections_visualization import edge_group

# Cosine function that is fit to Rabi oscillations
def cos_func(
    drive_amp: float,
    frequency: float,
    amplitude: float,
    offset: float,
    phase: float = 0,
) -> float:
    return amplitude * np.cos(2 * np.pi * frequency * (drive_amp + phase)) + offset

class ChevronModel(lmfit.model.Model):
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
        self.set_param_hint("swap", expr="1/(2*frequency)-phase", vary=False)
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

class CZChevronAnalysis():
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
        self.freq = self.dataset[f'cz_pulse_frequencies_sweep{self.qubit}'].values/1e6
        self.amp = self.dataset[f'cz_pulse_amplitudes{self.qubit}'].values
        magnitudes = self.dataset[f'y{self.qubit}'].values
        self.magnitudes = (magnitudes - np.min(magnitudes))/(np.max(magnitudes)-np.min(magnitudes))
        # values = [[np.linalg.norm(u) for u in v] for v in self.dataset[f'y{self.qubit}_']]
        fit_results = []
        for magnitude in self.magnitudes:
            model = ChevronModel()
            # magnitude = np.transpose(values)[15]
            fit_amplitudes = np.linspace( self.amp[0], self.amp[-1], 400)
            guess = model.guess(magnitude, drive_amp=self.amp)
            fit_result = model.fit(magnitude, params=guess, drive_amp=self.amp)
            fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: fit_amplitudes})
            fit_results.append(fit_result)
            # plt.plot(y,magnitude,'.r')
            # plt.plot(fit_amplitudes,fit_y,'--b')
        qois = np.transpose([[fit.result.params[p].value for p in ['amplitude','frequency']] for fit in fit_results])
        qois = np.transpose([(q-np.min(q))/np.max(q) for q in qois])
        opt_id = np.argmax(np.sum(qois,axis=1))
        self.opt_freq = self.freq[opt_id]
        self.opt_cz = fit_results[opt_id].result.params['cz'].value
        self.opt_swap = fit_results[opt_id].result.params['swap'].value

        return self.opt_freq

    def plotter(self,axis):
        datarray = self.dataset[f'y{self.qubit}']
        qubit = self.qubit
        #fig = datarray.plot(ax=axis, x=f'cz_pulse_frequencies_sweep{qubit}',cmap='RdBu_r')
        fig = axis.pcolormesh(self.amp,self.freq,self.magnitudes,shading='nearest',cmap='RdBu_r')
        axis.scatter(self.opt_cz,self.opt_freq,c='r',label = 'CZ Amplitude= {:.2f} V'.format(self.opt_cz),marker='X',s=200,edgecolors='k', linewidth=2,zorder=10)
        axis.scatter(self.opt_swap,self.opt_freq,c='b',label = 'SWAP Amplitude= {:.2f} V'.format(self.opt_swap),marker='X',s=200,edgecolors='k', linewidth=2,zorder=10)
        axis.hlines(self.opt_freq,self.amp[0],self.amp[-1],label = 'Frequency = {:.2f} MHz'.format(self.opt_freq),colors='k',linestyles='--',linewidth=2)
        axis.legend(loc = 'lower center', bbox_to_anchor=(-0.15, -0.45, 1.4, .102), mode='expand', ncol=2,
            title = 'Optimal Gate Parameters', columnspacing=200,borderpad=1)
        #cbar = axis.colorbar(fig)
        #cbar.set_label('Qubit Population', labelpad=10)
        axis.set_xlabel('Amplitude (V)')
        axis.set_ylabel('Frequency (MHz)')
        #axis.title(f'CZ Chevron {qubit}')
