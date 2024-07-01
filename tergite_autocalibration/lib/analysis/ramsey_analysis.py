import lmfit
import numpy as np
import xarray as xr
from quantify_core.analysis.fitting_models import exp_damp_osc_func, fft_freq_phase_guess

from tergite_autocalibration.config.settings import REDIS_CONNECTION
from tergite_autocalibration.lib.base.analysis import BaseAnalysis


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



class RamseyAnalysis(BaseAnalysis):
    def __init__(self, dataset: xr.Dataset, redis_field='clock_freqs:f01'):
        super().__init__()
        self.dataset = dataset
        self.model = RamseyModel()
        self.redis_field = redis_field
        self.qubit = dataset.attrs['qubit']
        redis_key = f'transmons:{self.qubit}'

        self.data_var = list(dataset.data_vars.keys())[0]
        for coord in dataset[self.data_var].coords:
            if 'delay' in coord:
                self.delay_coord = coord
            elif 'detuning' in coord:
                self.detuning_coord = coord

        if dataset.node == 'ramsey_correction_12':
            redis_field = 'clock_freqs:f12'
        self.qubit_frequency = float(REDIS_CONNECTION.hget(f'{redis_key}', redis_field))
        # print(redis_field,self.qubit_frequency)

    def run_fitting(self):
        self.ramsey_delays = self.dataset.coords[self.delay_coord].values
        self.fit_ramsey_delays = np.linspace(self.ramsey_delays[0], self.ramsey_delays[-1], 400)

        complex_values = self.dataset[self.data_var]
        self.magnitudes = np.array(np.absolute(complex_values.values).flat)
        artificial_detuning = self.dataset[self.detuning_coord].values[0]
        # complex_values = self.dataset[self.data_var].isel({self.detuning_coord: [indx]})

        guess = self.model.guess(self.magnitudes, t=self.ramsey_delays)
        fit_result = self.model.fit(self.magnitudes, params=guess, t=self.ramsey_delays)
        self.fit_y = self.model.eval(fit_result.params, **{self.model.independent_vars[0]: self.fit_ramsey_delays})

        fitted_detuning = fit_result.params['frequency'].value
        self.frequency_correction = fitted_detuning - artificial_detuning
        self.corrected_qubit_frequency = self.qubit_frequency - self.frequency_correction


        # fits = []
        # for indx, detuning in enumerate(self.dataset.coords[self.detuning_coord]):
        #     complex_values = self.dataset[self.data_var].isel({self.detuning_coord: [indx]})
        #     magnitudes = np.array(np.absolute(complex_values.values).flat)
        #     guess = model.guess(magnitudes, t=ramsey_delays)
        #     fit_result = model.fit(magnitudes, params=guess, t=ramsey_delays)
        #     fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_ramsey_delays})
        #     fitted_detuning = fit_result.params['frequency'].value
        #     fits.append(fitted_detuning)
        # fits = np.array(fits)




        # index_of_min = np.argmin(fits)
        # self.fitted_detunings = np.concatenate((fits[:index_of_min] * (-1), fits[index_of_min:]))

        # m, b = np.polyfit(self.artificial_detunings, self.fitted_detunings, 1)
        # self.poly1d_fn = np.poly1d((m, b))
        # self.frequency_correction = -b / m

        # print("Frequency before correction: ", self.qubit_frequency)
        self.corrected_qubit_frequency = self.qubit_frequency + self.frequency_correction
        # print("Frequency after correction: ", self.corrected_qubit_frequency)
        return [self.corrected_qubit_frequency]

    def plotter(self, ax):
        # ax.plot(self.artificial_detunings, self.fitted_detunings, 'bo', ms=5.0)
        # self.dataset[self.data_var].plot(ax=ax, x=self.delay_coord)
        ax.plot( self.fit_ramsey_delays , self.fit_y,'r-',lw=3.0)
        ax.plot( self.ramsey_delays, self.magnitudes,'bo-',ms=3.0)
        # ax.set_title(f'Ramsey Oscillations for {self.qubit}')
        # ax.axvline(self.frequency_correction, color='red',
        #            label=f'correction: {int(self.frequency_correction) / 1e3} kHz')
        # ax.plot(self.artificial_detunings, self.poly1d_fn(self.artificial_detunings), '--b', lw=1)
        # ax.axvline(0, color='black', lw=1)
        # ax.set_xlabel('Artificial detuning (Hz)')
        # ax.set_ylabel('Fitted detuning (Hz)')
        ax.grid()


class RamseyDetuningsAnalysis(BaseAnalysis):
    def __init__(self, dataset: xr.Dataset, redis_field='clock_freqs:f01'):
        super().__init__()
        self.redis_field = redis_field
        self.qubit = dataset.attrs['qubit']
        redis_key = f'transmons:{self.qubit}'

        self.data_var = list(dataset.data_vars.keys())[0]
        coord = list(dataset[self.data_var].coords.keys())[0]
        for coord in dataset[self.data_var].coords:
            if 'delay' in coord:
                self.delay_coord = coord
            elif 'detuning' in coord:
                self.detuning_coord = coord
        self.artificial_detunings = dataset.coords[self.detuning_coord].values
        dataset[self.data_var] = ((self.delay_coord, self.detuning_coord), np.abs(dataset[self.data_var].values))
        self.S21 = dataset[self.data_var].values
        self.fit_results = {}
        # print(dataset)
        if dataset.node == 'ramsey_correction_12':
            redis_field = 'clock_freqs:f12'
        self.qubit_frequency = float(REDIS_CONNECTION.hget(f'{redis_key}', redis_field))
        # print(redis_field,self.qubit_frequency)
        self.dataset = dataset

    def run_fitting(self):
        model = RamseyModel()
        ramsey_delays = self.dataset.coords[self.delay_coord].values
        self.fit_ramsey_delays = np.linspace(ramsey_delays[0], ramsey_delays[-1], 400)

        fits = []
        for indx, detuning in enumerate(self.dataset.coords[self.detuning_coord]):
            complex_values = self.dataset[self.data_var].isel({self.detuning_coord: [indx]})
            magnitudes = np.array(np.absolute(complex_values.values).flat)
            guess = model.guess(magnitudes, t=ramsey_delays)
            fit_result = model.fit(magnitudes, params=guess, t=ramsey_delays)
            fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_ramsey_delays})
            fitted_detuning = fit_result.params['frequency'].value
            fits.append(fitted_detuning)
        fits = np.array(fits)
        index_of_min = np.argmin(fits)
        self.fitted_detunings = np.concatenate((fits[:index_of_min] * (-1), fits[index_of_min:]))

        m, b = np.polyfit(self.artificial_detunings, self.fitted_detunings, 1)
        self.poly1d_fn = np.poly1d((m, b))
        self.frequency_correction = -b / m

        # self.dataset['fit_ramsey_delays'] = self.fit_ramsey_delays
        # self.dataset['fit_y'] = ('fit_ramsey_delays',fit_y)
        # print("Frequency before correction: ", self.qubit_frequency)
        self.corrected_qubit_frequency = self.qubit_frequency + self.frequency_correction
        # print("Frequency after correction: ", self.corrected_qubit_frequency)
        return [self.corrected_qubit_frequency]

    def plotter(self, ax):
        ax.plot(self.artificial_detunings, self.fitted_detunings, 'bo', ms=5.0)
        # self.dataset[self.data_var].plot(ax=ax, x=self.delay_coord)
        # ax.plot( self.fit_ramsey_delays , self.fit_y,'r-',lw=3.0)
        # ax.plot( self.independents, self.magnitudes,'bo-',ms=3.0)
        # ax.set_title(f'Ramsey Oscillations for {self.qubit}')
        ax.axvline(self.frequency_correction, color='red',
                   label=f'correction: {int(self.frequency_correction) / 1e3} kHz')
        ax.plot(self.artificial_detunings, self.poly1d_fn(self.artificial_detunings), '--b', lw=1)
        ax.axvline(0, color='black', lw=1)
        ax.set_xlabel('Artificial detuning (Hz)')
        ax.set_ylabel('Fitted detuning (Hz)')

        ax.grid()
