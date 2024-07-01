import lmfit
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from numpy.linalg import inv
from quantify_core.analysis.fitting_models import fft_freq_phase_guess
from scipy.linalg import norm
from scipy.optimize import minimize
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import confusion_matrix

from tergite_autocalibration.config.coupler_config import qubit_types
from tergite_autocalibration.lib.base.analysis import BaseAnalysis


# Cosine function that is fit to Rabi oscillations
def cos_func(
        drive_amp: float,
        frequency: float,
        amplitude: float,
        offset: float,
        phase: float = 0,
) -> float:
    return amplitude * np.cos(2 * np.pi * frequency * (drive_amp + phase)) + offset


def mitigate(v, cm_inv):
    u = np.dot(v, cm_inv)

    # print(u,np.sum(u))
    def m(t):
        return norm(u - np.array(t))

    def con(t):
        return t[0] + t[1] + t[2] - 1

    cons = ({'type': 'eq', 'fun': con},
            {'type': 'ineq', 'fun': lambda t: t[0]},
            {'type': 'ineq', 'fun': lambda t: t[1]},
            {'type': 'ineq', 'fun': lambda t: t[2]})
    result = minimize(m, v, method='SLSQP', constraints=cons)
    w = np.abs(np.round(result.x, 10))
    # print(w)
    return w


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
        self.set_param_hint("phase", min=-360, max=360)

        # Pi-pulse amplitude can be derived from the oscillation frequency

        # self.set_param_hint("swap", expr="1/(2*frequency)-phase", vary=False)
        self.set_param_hint("cz", expr="(2/(2*frequency)-phase)", vary=False)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        drive_amp = kws.get("drive_amp", None)
        if drive_amp is None:
            return None

        amp_guess = abs(max(data) - min(data)) / 2  # amp is positive by convention
        offs_guess = np.mean(data)

        # breakpoint()    

        # Frequency guess is obtained using a fast fourier transform (FFT).
        (freq_guess, _) = fft_freq_phase_guess(data, drive_amp)

        self.set_param_hint("frequency", value=freq_guess, min=freq_guess * 0.9)
        self.set_param_hint("amplitude", value=amp_guess, min=amp_guess * 0.9)
        self.set_param_hint("offset", value=offs_guess)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)


class CZCalibrationAnalysis(BaseAnalysis):
    def __init__(self, dataset: xr.Dataset):
        super().__init__()
        data_var = list(dataset.data_vars.keys())[0]
        coord = list(dataset[data_var].coords.keys())[0]
        self.S21 = dataset[data_var].values
        self.independents = dataset[coord].values
        self.fit_results = {}
        self.qubit = dataset[data_var].attrs['qubit']

        measurements = self.S21
        data = measurements[:-2]
        calibration_0 = measurements[-2]
        calibration_1 = measurements[-1]
        displacement_vector = calibration_1 - calibration_0
        data_translated_to_zero = data - calibration_0

        rotation_angle = np.angle(displacement_vector)
        rotated_data = data_translated_to_zero * np.exp(-1j * rotation_angle)
        rotated_0 = calibration_0 * np.exp(-1j * rotation_angle)
        rotated_1 = calibration_1 * np.exp(-1j * rotation_angle)
        normalization = (rotated_1 - rotated_0).real
        real_rotated_data = rotated_data.real
        self.data =  real_rotated_data / normalization
        self.dataset = dataset

    def run_fitting(self):
        # self.testing_group = 0
        self.dynamic = self.dataset.attrs['node'][:16] == 'cz_dynamic_phase'
        self.swap = self.dataset.attrs['node'][-4:] == 'swap'
        qubit_type_list = ['Control','Target']
        if self.swap:
            qubit_type_list.reverse() 

        self.freq = self.dataset[f'control_ons{self.qubit}'].values
        self.amp = self.dataset[f'ramsey_phases{self.qubit}'].values[:-2]
        magnitudes = self.data
        self.magnitudes = np.transpose(magnitudes)
        # self.magnitudes = np.transpose((magnitudes - np.min(magnitudes))/(np.max(magnitudes)-np.min(magnitudes)))
        self.fit_amplitudes = np.linspace(self.amp[0], self.amp[-1], 400)

        self.fit_results, self.fit_ys = [], []

        for magnitude in self.magnitudes:
            if qubit_types[self.qubit] == qubit_type_list[1]:
                fit = True
                model = CZModel()
                # magnitude = np.transpose(values)[15]
                guess = model.guess(magnitude, drive_amp=self.amp)
                fit_result = model.fit(magnitude, params=guess, drive_amp=self.amp)
                fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_amplitudes})
                self.fit_results.append(fit_result)
            else:
                fit = False
                fit_y = [np.mean(magnitude)] * 400
            self.fit_ys.append(fit_y)
        if fit:
            try:
                qois = np.transpose(
                    [[[fit.result.params[p].value, fit.result.params[p].stderr] for p in ['cz']] for fit in
                        self.fit_results])
                self.opt_cz = qois[0][0]
                self.cphase = 180 - np.abs(np.abs(np.diff(self.opt_cz))[0] - 180)
                # self.cphase = np.abs(np.diff(self.opt_cz))[0]
                print(qois)
                self.err = np.sqrt(np.sum(np.array(qois[1][0]) ** 2))
            except:
                print('fitting failed ....')
                self.cphase = 0
                self.err = 0
                self.opt_cz = [0] * 2

        else:
            self.cphase = 0
            self.err = 0
            self.opt_cz = [0] * 2
        if fit:
            qois = np.transpose(
                [[[fit.result.params[p].value, fit.result.params[p].stderr] for p in ['amplitude']] for fit in
                    self.fit_results])
            self.pop_loss = np.diff(np.flip(qois[0][0]),axis=0)[0]
        else:
            self.pop_loss = np.diff(np.mean(self.fit_ys,axis=1))[0]

        return [self.cphase, self.pop_loss]

    def plotter(self, axis):
        # datarray = self.dataset[f'y{self.qubit}']
        # qubit = self.qubit

        if self.dynamic:
            label = ['Gate Off', 'Gate On']
            name = 'Dynamic Phase'
        else:
            label = ['Control Off', 'Control On']
            name = 'CZ'
        x = range(len(label))
        colors = plt.get_cmap('RdBu_r')(np.linspace(0.2, 0.8, len(x)))
        for index, magnitude in enumerate(self.magnitudes):
            axis.plot(self.amp, magnitude, '.', c=colors[index])
            axis.plot(self.fit_amplitudes, self.fit_ys[index], '-', c=colors[index], label=label[index])
            axis.vlines(self.opt_cz[index], -10, 10, colors='gray', linestyles='--', linewidth=1.5)

        axis.vlines(0, -10, -10, colors='gray', linestyles='--',
                    label='{:} = {:.1f}+/-{:.1f} \n pop_loss = {:.2f}'.format(name, self.cphase, self.err,self.pop_loss), zorder=-10)
        
        # axis.legend(loc = 'upper right')
        axis.set_xlim([self.amp[0], self.amp[-1]])
        axis.set_ylim(np.min(self.magnitudes), np.max(self.magnitudes))
        axis.set_xlabel('Phase (deg)')
        axis.set_ylabel('Population')
        axis.set_title(f'{name} Calibration - {qubit_types[self.qubit]} Qubit {self.qubit[1:]}')


class CZCalibrationSSROAnalysis(BaseAnalysis):
    def __init__(self, dataset: xr.Dataset):
        super().__init__()
        self.data_var = list(dataset.data_vars.keys())[0]
        self.qubit = dataset[self.data_var].attrs['qubit']
        for coord in dataset.coords:
            if f'control_ons{self.qubit}' in str(coord):
                self.sweep_coord = coord
            elif f'ramsey_phases{self.qubit}' in str(coord):
                self.state_coord = coord
            elif 'shot' in str(coord):
                self.shot_coord = coord

        self.independents = np.array([float(val) for val in dataset[self.state_coord].values[:-3]])
        self.calibs = dataset[self.state_coord].values[-3:]
        self.sweeps = dataset.coords[self.sweep_coord]
        self.shots = len(dataset[self.shot_coord].values)
        self.fit_results = {}

        self.dataset = dataset

    def run_fitting(self):
        # self.testing_group = 0
        self.dynamic = self.dataset.attrs['node'] == 'cz_dynamic_phase'
        self.swap = self.dataset.attrs['node'][15:19] == 'swap'
        qubit_type_list = ['Control','Target']
        if self.swap:
            qubit_type_list.reverse() 
        self.all_magnitudes = []
        for indx, _ in enumerate(self.sweeps):
            # Calculate confusion matrix from calibration shots
            y = np.repeat(self.calibs, self.shots)
            IQ_complex = np.array([])
            for state, _ in enumerate(self.calibs):
                IQ_complex_0 = self.dataset[self.data_var].isel({self.sweep_coord: indx, self.state_coord: -3 + state})
                IQ_complex = np.append(IQ_complex, IQ_complex_0)
            I = IQ_complex.real.flatten()
            Q = IQ_complex.imag.flatten()
            IQ = np.array([I, Q]).T
            # IQ = IQ_complex.reshape(-1,2)
            # breakpoint()
            lda = LinearDiscriminantAnalysis(solver="svd", store_covariance=True)
            cla = lda.fit(IQ, y)
            y_pred = cla.predict(IQ)

            cm = confusion_matrix(y, y_pred)
            cm_norm = confusion_matrix(y, y_pred, normalize='true')
            cm_inv = inv(cm_norm)
            assignment = np.trace(cm_norm) / len(self.calibs)
            # print(f'{assignment = }')
            # print(f'{cm_norm = }')
            # disp = ConfusionMatrixDisplay(confusion_matrix=cm_norm)
            # disp.plot()
            # plt.show()

            # Classify data shots
            raw_data = self.dataset[self.data_var].isel({self.sweep_coord: indx}).values
            raw_shape = raw_data.shape
            I = raw_data.real.flatten()
            Q = raw_data.imag.flatten()
            IQ = np.array([I, Q]).T
            data_y_pred = cla.predict(IQ.reshape(-1, 2))
            # breakpoint()
            data_y_pred = np.transpose(data_y_pred.reshape(raw_shape))
            data_res_shape = list(data_y_pred.shape[:-1])
            data_res_shape.append(len(self.calibs))

            data_res = np.array([])
            for sweep in data_y_pred:
                uniques, counts = np.unique(sweep, return_counts=True)
                #print('unique elements are: ', uniques)
                if len(counts) == 1:
                    counts = np.append(counts, 0)
                elif len(counts) == 2 and uniques[1] == 'c2':
                    pop2 = counts[1]
                    counts[1] = 0
                    counts = np.append(counts, pop2)
                elif len(counts) == 2:
                    counts = np.append(counts, 0)

                raw_prob = counts / len(sweep)
                mitigate_prob = mitigate(raw_prob, cm_inv)
                data_res = np.append(data_res, mitigate_prob)
            data_res = data_res.reshape(data_res_shape)
            self.all_magnitudes.append(data_res)
        self.all_magnitudes = np.array(self.all_magnitudes)
        # Fitting the 0 state data
        self.magnitudes = self.all_magnitudes[:, :-3, 1]

        self.fit_independents = np.linspace(self.independents[0], self.independents[-1], 400)
        self.fit_results, self.fit_ys = [], []
        try:
            for magnitude in self.magnitudes:
                if qubit_types[self.qubit] == qubit_type_list[1]:
                    # Odd qubits are target qubits
                    fit = True
                    model = CZModel()
                    # magnitude = np.transpose(values)[15]
                    # breakpoint()
                    guess = model.guess(magnitude, drive_amp=self.independents)
                    fit_result = model.fit(magnitude, params=guess, drive_amp=self.independents)
                    fit_y = model.eval(fit_result.params, **{model.independent_vars[0]: self.fit_independents})
                    self.fit_results.append(fit_result)
                else:
                    # Even qubits are control qubits
                    fit = False
                    fit_y = [np.mean(magnitude)] * 400
                self.fit_ys.append(fit_y)
            if fit:
                qois = np.transpose(
                    [[[fit.result.params[p].value, fit.result.params[p].stderr] for p in ['cz']] for fit in
                     self.fit_results])
                self.opt_cz = qois[0][0]
                self.cphase = 180 - np.abs(np.abs(np.diff(self.opt_cz))[0] - 180)
                # print(qois)    
                self.err = np.sqrt(np.sum(np.array(qois[1][0]) ** 2))
            else:
                self.cphase = 0
                self.err = 0
                self.opt_cz = [0] * 2
        except:
            self.cphase = 0
            self.err = 0
            self.opt_cz = [0] * 2
        # self.cphase = 0
        if fit:
            qois = np.transpose(
                [[[fit.result.params[p].value, fit.result.params[p].stderr] for p in ['amplitude']] for fit in
                 self.fit_results])
            self.pop_loss = np.diff(np.flip(qois[0][0]))[0]
        else:
            self.pop_loss = np.diff(np.mean(self.fit_ys,axis=1))[0]
            #self.pop_loss = np.mean(np.diff(np.flip(self.fit_ys)))
        self.leakage = np.diff(np.flip(np.mean(self.all_magnitudes[:, :-3, 2], axis=1)))[0]
        return [self.cphase, self.pop_loss, self.leakage]

    def plotter(self, axis):
        # datarray = self.dataset[f'y{self.qubit}']
        # qubit = self.qubit

        if self.dynamic:
            label = ['Gate Off', 'Gate On']
            name = 'Dynamic Phase'
        else:
            label = ['Control Off', 'Control On']
            name = 'CZ'
        x = range(len(label))
        marker = ['.', '*', '1', '--']
        colors = plt.get_cmap('RdBu_r')(np.linspace(0.2, 0.8, len(x)))
        # colors = plt.get_cmap('tab20c')

        for index, magnitude in enumerate(self.all_magnitudes):
            axis.plot(self.independents, magnitude[:-3, 1], f'{marker[0]}', c=colors[index],
                      label=f'|1> {label[index]}')
            # axis.plot(self.independents,magnitude[:-3,1],f'{marker[index]}',c = colors(2+4),label=f'|1> {label[index]}')
            axis.plot(self.independents, magnitude[:-3, 2], f'{marker[1]}', c=colors[index],
                      label=f'|2> {label[index]}')
            axis.plot(self.independents, magnitude[:-3, 0], f'{marker[2]}', c=colors[index],
                    label=f'0> {label[index]}')           

        for index, magnitude in enumerate(self.magnitudes):
            axis.plot(self.fit_independents, self.fit_ys[index], '-', c=colors[index])
            axis.vlines(self.opt_cz[index], -10, 10, colors='gray', linestyles='--', linewidth=1.5)

        axis.vlines(0, -10, -10, colors='gray', linestyles='--',
                    label='{:} = {:.1f}+/-{:.1f} \n pop_loss = {:.2f}'.format(name, self.cphase, self.err,self.pop_loss), zorder=-10)
        axis.set_xlim([self.independents[0], self.independents[-1]])
        axis.legend(loc='upper right')
        axis.set_ylim(-0.01, 1.01)
        axis.set_xlabel('Phase (deg)')
        axis.set_ylabel('Population')
        axis.set_title(f'{name} Calibration - {qubit_types[self.qubit]} Qubit {self.qubit[1:]}')
