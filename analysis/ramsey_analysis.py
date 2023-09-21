import numpy as np
import lmfit
import xarray as xr
import redis
from quantify_core.analysis.fitting_models import exp_damp_osc_func, fft_freq_phase_guess

redis_connection = redis.Redis(decode_responses=True)

class RamseyModel(lmfit.model.Model):
    def __init__(self, *args, **kwargs):
        # pass in the defining equation so the user doesn't have to later.
        super().__init__(exp_damp_osc_func, *args, **kwargs)

        # Enforce oscillation frequency is positive
        self.set_param_hint("frequency", min=0)
        # Enforce amplitude is positive
        self.set_param_hint("amplitude", min=0)
        # Enforce decay time is positive
        self.set_param_hint("tau", min=0)

        # Fix the n_factor at 1
        self.set_param_hint("n_factor", expr="1", vary=False)


    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        t = kws.get("t", None)
        if t is None:
            raise ValueError(
                'Time variable "t" must be specified in order to guess parameters'
            )
            return None

        amp_guess = abs(max(data) - min(data)) / 2  # amp is positive by convention
        exp_offs_guess = np.mean(data)
        tau_guess = 2 / 3 * np.max(t)

        (freq_guess, phase_guess) = fft_freq_phase_guess(data, t)

        self.set_param_hint("frequency", value=freq_guess, min=0)
        self.set_param_hint("amplitude", value=amp_guess, min=0)
        self.set_param_hint("offset", value=exp_offs_guess)
        self.set_param_hint("phase", value=phase_guess)
        self.set_param_hint("tau", value=tau_guess, min=0)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)



class RamseyAnalysis():
    def  __init__( self,dataset: xr.Dataset, redis_field='freq_01'):
        this_qubit = dataset.attrs['qubit']
        redis_key = f'transmons:{this_qubit}'

        data_var = list(dataset.data_vars.keys())[0]
        coord = list(dataset[data_var].coords.keys())[0]
        self.S21 = dataset[data_var].values
        self.independents = dataset[coord].values
        for coord in dataset[data_var].coords:
            if 'delay' in coord: self.delay_coord = coord
            elif 'detuning' in coord: self.detuning_coord = coord
        self.fit_results = {}
        breakpoint()
        self.qubit = dataset[data_var].attrs['qubit']
        self.qubit_frequency = float(redis_connection.hget(f'{redis_key}',redis_field))
        self.dataset = dataset

    def run_fitting(self):
        # model = RamseyModel()
        # self.magnitudes = np.absolute(self.S21)
        # ramsey_delays = self.independents
        # self.fit_ramsey_delays = np.linspace(ramsey_delays[0], ramsey_delays[-1], 400)
        #
        # guess = model.guess(self.magnitudes, t=ramsey_delays)
        # # print(f'{ guess = }')
        # fit_result = model.fit(self.magnitudes, params=guess, t=ramsey_delays)
        #
        # self.fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_ramsey_delays})
        # # self.dataset['fit_ramsey_delays'] = self.fit_ramsey_delays
        # # self.dataset['fit_y'] = ('fit_ramsey_delays',fit_y)
        # self.fitted_detuning = fit_result.params['frequency'].value
        # # print(f'{ self.qubit_frequency/1e6 = }')
        # # print(f'{ self.fitted_detuning/1e6 = }')
        # # print(f'{ self.artificial_detuning/1e6 = }')
        # self.corrected_qubit_frequency = self.qubit_frequency - (self.fitted_detuning - self.artificial_detuning)
        # return self.corrected_qubit_frequency
        return 0

    def plotter(self,ax):
        self.dataset.plot(ax=ax, x='self.delay_coord')
        # ax.plot( self.fit_ramsey_delays , self.fit_y,'r-',lw=3.0)
        # ax.plot( self.independents, self.magnitudes,'bo-',ms=3.0)
        # ax.set_title(f'Ramsey Oscillations for {self.qubit}')
        # ax.set_xlabel('Intermediate (s)')
        # ax.set_ylabel('|S21| (V)')
        # ax.grid()
