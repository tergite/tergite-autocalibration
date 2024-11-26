# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Amr Osman 2024
# (C) Copyright Michele Faucci Giannelli 2024
# (C) Copyright Chalmers Next Labs AB 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import itertools

import lmfit
import numpy as np
import xarray as xr
from matplotlib import pyplot as plt
from numpy.linalg import inv
from quantify_core.analysis.fitting_models import fft_freq_phase_guess
from scipy.linalg import norm
from scipy.optimize import minimize
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import confusion_matrix

from tergite_autocalibration.config.legacy import dh
from tergite_autocalibration.lib.base.analysis import (
    BaseAllQubitsAnalysis,
    BaseAnalysis,
    BaseQubitAnalysis,
)


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

    def m(t):
        return norm(u - np.array(t))

    def con(t):
        return t[0] + t[1] + t[2] - 1

    cons = (
        {"type": "eq", "fun": con},
        {"type": "ineq", "fun": lambda t: t[0]},
        {"type": "ineq", "fun": lambda t: t[1]},
        {"type": "ineq", "fun": lambda t: t[2]},
    )
    result = minimize(m, v, method="SLSQP", constraints=cons)
    w = np.abs(np.round(result.x, 10))

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

        # Frequency guess is obtained using a fast fourier transform (FFT).
        (freq_guess, _) = fft_freq_phase_guess(data, drive_amp)

        self.set_param_hint("frequency", value=freq_guess, min=freq_guess * 0.9)
        self.set_param_hint("amplitude", value=amp_guess, min=amp_guess * 0.9)
        self.set_param_hint("offset", value=offs_guess)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)


class CZCalibrationSSROQubitAnalysis(BaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def analyse_qubit(self):
        for coord in self.dataset.coords:
            if f"control_ons" in str(coord):
                self.sweep_coord = coord
            elif f"ramsey_phases" in str(coord):
                self.state_coord = coord
            elif "shot" in str(coord):
                self.shot_coord = coord

        self.independents = np.array(
            [float(val) for val in self.dataset[self.state_coord].values[:-3]]
        )
        self.calibs = self.dataset[self.state_coord].values[-3:]
        self.sweeps = self.dataset.coords[self.sweep_coord]
        self.shots = len(self.dataset[self.shot_coord].values)
        self.fit_results = {}

        # self.testing_group = 0
        self.dynamic = self.dataset.attrs["node"] == "cz_dynamic_phase"
        self.swap = self.dataset.attrs["node"][15:19] == "swap"
        qubit_type_list = ["Control", "Target"]
        if self.swap:
            qubit_type_list.reverse()
        self.all_magnitudes = []
        for indx, _ in enumerate(self.sweeps):
            # Calculate confusion matrix from calibration shots
            y = np.repeat(self.calibs, self.shots)
            IQ_complex = np.array([])
            for state, _ in enumerate(self.calibs):
                IQ_complex_0 = self.magnitudes[self.data_var].isel(
                    {self.sweep_coord: indx, self.state_coord: -3 + state}
                )
                IQ_complex = np.append(IQ_complex, IQ_complex_0)
            I = IQ_complex.real.flatten()
            Q = IQ_complex.imag.flatten()
            IQ = np.array([I, Q]).T
            lda = LinearDiscriminantAnalysis(solver="svd", store_covariance=True)
            cla = lda.fit(IQ, y)
            y_pred = cla.predict(IQ)

            cm = confusion_matrix(y, y_pred)
            cm_norm = confusion_matrix(y, y_pred, normalize="true")
            cm_inv = inv(cm_norm)
            assignment = np.trace(cm_norm) / len(self.calibs)

            # Classify data shots
            raw_data = (
                self.magnitudes[self.data_var].isel({self.sweep_coord: indx}).values
            )
            raw_shape = raw_data.shape
            I = raw_data.real.flatten()
            Q = raw_data.imag.flatten()
            IQ = np.array([I, Q]).T
            data_y_pred = cla.predict(IQ.reshape(-1, 2))
            data_y_pred = np.transpose(data_y_pred.reshape(raw_shape))
            data_res_shape = list(data_y_pred.shape[:-1])
            data_res_shape.append(len(self.calibs))

            data_res = np.array([])
            for sweep in data_y_pred:
                uniques, counts = np.unique(sweep, return_counts=True)
                raw_prob = [0] * len(self.calibs)
                for state_id, state in enumerate(uniques):
                    raw_prob[int(state)] = counts[state_id] / len(sweep)
                mitigate_prob = mitigate(raw_prob, cm_inv)
                data_res = np.append(data_res, mitigate_prob)
            data_res = data_res.reshape(data_res_shape)
            self.all_magnitudes.append(data_res)
        self.all_magnitudes = np.array(self.all_magnitudes)
        # Fitting the 0 state data
        self.magnitudes = self.all_magnitudes[:, :-3, 1]

        self.fit_independents = np.linspace(
            self.independents[0], self.independents[-1], 400
        )
        self.fit_results, self.fit_ys = [], []
        try:
            for magnitude in self.magnitudes:
                if dh.get_legacy("qubit_types")[self.qubit] == qubit_type_list[1]:
                    # Odd qubits are target qubits
                    fit = True
                    model = CZModel()
                    # magnitude = np.transpose(values)[15]
                    guess = model.guess(magnitude, drive_amp=self.independents)
                    fit_result = model.fit(
                        magnitude, params=guess, drive_amp=self.independents
                    )
                    fit_y = model.eval(
                        fit_result.params,
                        **{model.independent_vars[0]: self.fit_independents},
                    )
                    self.fit_results.append(fit_result)
                else:
                    # Even qubits are control qubits
                    fit = False
                    fit_y = [np.mean(magnitude)] * 400
                self.fit_ys.append(fit_y)
            if fit:
                qois = np.transpose(
                    [
                        [
                            [fit.result.params[p].value, fit.result.params[p].stderr]
                            for p in ["cz"]
                        ]
                        for fit in self.fit_results
                    ]
                )
                self.opt_cz = qois[0][0]
                self.cphase = 180 - np.abs(np.abs(np.diff(self.opt_cz))[0] - 180)
                self.err = np.sqrt(np.sum(np.array(qois[1][0]) ** 2))
            else:
                self.cphase = 0
                self.err = 0
                self.opt_cz = [0] * 2
        except:
            self.cphase = 0
            self.err = 0
            self.opt_cz = [0] * 2
        if fit:
            qois = np.transpose(
                [
                    [
                        [fit.result.params[p].value, fit.result.params[p].stderr]
                        for p in ["amplitude"]
                    ]
                    for fit in self.fit_results
                ]
            )
            try:
                self.pop_loss = np.diff(np.flip(qois[0][0]))[0]
            except:
                self.pop_loss = 1
        else:
            self.pop_loss = np.diff(np.mean(self.fit_ys, axis=1))[0]
        self.leakage = np.diff(
            np.flip(np.mean(self.all_magnitudes[:, :-3, 2], axis=1))
        )[0]
        return [self.cphase, self.pop_loss, self.leakage]

    def plotter(self, axis):
        if self.dynamic:
            label = ["Gate Off", "Gate On"]
            name = "Dynamic Phase"
        else:
            label = ["Control Off", "Control On"]
            name = "CZ"
        x = range(len(label))
        marker = [".", "*", "1", "--"]
        colors = plt.get_cmap("RdBu_r")(np.linspace(0.2, 0.8, len(x)))

        for index, magnitude in enumerate(self.all_magnitudes):
            axis.plot(
                self.independents,
                magnitude[:-3, 1],
                f"{marker[0]}",
                c=colors[index],
                label=f"|1> {label[index]}",
            )
            axis.plot(
                self.independents,
                magnitude[:-3, 2],
                f"{marker[1]}",
                c=colors[index],
                label=f"|2> {label[index]}",
            )

        for index, magnitude in enumerate(self.magnitudes):
            try:
                axis.plot(
                    self.fit_independents, self.fit_ys[index], "-", c=colors[index]
                )
            except:
                pass
            axis.vlines(
                self.opt_cz[index],
                -10,
                10,
                colors="gray",
                linestyles="--",
                linewidth=1.5,
            )

        axis.vlines(
            0,
            -10,
            -10,
            colors="gray",
            linestyles="--",
            label="{:} = {:.1f}+/-{:.1f} \n pop_loss = {:.2f}".format(
                name, self.cphase, self.err, self.pop_loss
            ),
            zorder=-10,
        )
        axis.set_xlim([self.independents[0], self.independents[-1]])
        axis.legend(loc="upper right")
        axis.set_ylim(-0.01, 1.01)
        axis.set_xlabel("Phase (deg)")
        axis.set_ylabel("Population")
        axis.set_title(
            f"{name} Calibration - {dh.get_legacy('qubit_types')[self.qubit]} Qubit {self.qubit[1:]}"
        )


class ResetCalibrationSSROQubitAnalysis(BaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def analyse_qubit(self):
        for coord in self.dataset.coords:
            if f"control_ons{self.qubit}" in str(coord):
                self.sweep_coord = coord
            elif f"ramsey_phases{self.qubit}" in str(coord):
                self.state_coord = coord
            elif "shot" in str(coord):
                self.shot_coord = coord

        self.independents = np.array(
            [float(val) for val in self.dataset[self.state_coord].values[:-3]]
        )
        self.calibs = self.dataset[self.state_coord].values[-3:]
        self.sweeps = self.dataset.coords[self.sweep_coord]
        self.shots = len(self.dataset[self.shot_coord].values)
        self.fit_results = {}

        self.dynamic = self.dataset.attrs["node"] == "cz_dynamic_phase"
        self.all_magnitudes = []
        for indx, _ in enumerate(self.sweeps):
            # Calculate confusion matrix from calibration shots
            y = np.repeat(self.calibs, self.shots)
            IQ_complex = np.array([])
            for state, _ in enumerate(self.calibs):
                IQ_complex_0 = self.S21[self.data_var].isel(
                    {self.sweep_coord: indx, self.state_coord: -3 + state}
                )
                IQ_complex = np.append(IQ_complex, IQ_complex_0)
            I = IQ_complex.real.flatten()
            Q = IQ_complex.imag.flatten()
            IQ = np.array([I, Q]).T

            lda = LinearDiscriminantAnalysis(solver="svd", store_covariance=True)
            cla = lda.fit(IQ, y)
            y_pred = cla.predict(IQ)

            cm = confusion_matrix(y, y_pred)
            cm_norm = confusion_matrix(y, y_pred, normalize="true")
            cm_inv = inv(cm_norm)
            assignment = np.trace(cm_norm) / len(self.calibs)

            # Classify data shots
            raw_data = self.S21[self.data_var].isel({self.sweep_coord: indx}).values
            raw_shape = raw_data.shape
            I = raw_data.real.flatten()
            Q = raw_data.imag.flatten()
            IQ = np.array([I, Q]).T
            data_y_pred = cla.predict(IQ.reshape(-1, 2))
            data_y_pred = np.transpose(data_y_pred.reshape(raw_shape))
            data_res_shape = list(data_y_pred.shape[:-1])
            data_res_shape.append(len(self.calibs))

            data_res = np.array([])
            for sweep in data_y_pred:
                uniques, counts = np.unique(sweep, return_counts=True)
                raw_prob = [0] * len(self.calibs)
                for state_id, state in enumerate(uniques):
                    raw_prob[int(state)] = counts[state_id] / len(sweep)
                raw_prob = counts / len(sweep)
                mitigate_prob = mitigate(raw_prob, cm_inv)
                data_res = np.append(data_res, mitigate_prob)
            data_res = data_res.reshape(data_res_shape)
            self.all_magnitudes.append(data_res)
        self.all_magnitudes = np.array(self.all_magnitudes)

        # Fitting the 1 state data
        self.magnitudes = self.all_magnitudes[:, :-3, 1]
        self.f_magnitudes = self.all_magnitudes[:, :-3, 2]

        self.fit_independents = self.independents
        self.fit_ys = []

        for n, magnitude in enumerate(self.magnitudes):
            if dh.get_legacy("qubit_types")[self.qubit] == "Target":
                if n == 0:
                    self.fit_ys.append(
                        [0, 0, 0, 1, 1, 1, 0, 0, 0]
                    )  # Control - ResetOff
                else:
                    self.fit_ys.append([0, 0, 0, 0, 0, 0, 0, 0, 0])  # Target - ResetOn
            else:
                if n == 0:
                    self.fit_ys.append([0, 1, 0, 0, 1, 0, 0, 1, 0])  # Target - ResetOff
                else:
                    self.fit_ys.append(
                        [0, 1, 0, 0, 1, 0, 0, 1, 0]
                    )  # Target - ResetOn no leakage reduction

        self.fit_ys = np.array(self.fit_ys)
        self.pop_loss = 1 - np.sum(np.abs(self.magnitudes - self.fit_ys)) / 9
        self.leakage = np.mean(self.f_magnitudes[-1])
        magnitudes_str = ",".join(
            str(element) for element in list(self.magnitudes.flatten())
        )
        f_magnitudes_str = ",".join(
            str(element) for element in list(self.f_magnitudes.flatten())
        )
        return [self.pop_loss, self.leakage, magnitudes_str, f_magnitudes_str]

    def plotter(self, axis):
        state = ["0", "1", "2"]
        states = list(itertools.product(state, state))
        states = [state[0] + state[1] for state in states]

        label = ["Reset Off", "Reset On"]
        name = "Reset"
        x = range(len(label))
        marker = [".", "*", "-", "--"]
        colors = plt.get_cmap("RdBu_r")(np.linspace(0.2, 0.8, len(x)))
        # colors = plt.get_cmap('tab20c')

        for index, magnitude in enumerate(self.all_magnitudes):
            axis.plot(
                self.independents,
                magnitude[:-3, 1],
                f"{marker[0]}",
                c=colors[index],
                label=f"|1> {label[index]}",
            )
            axis.plot(
                self.independents,
                magnitude[:-3, 2],
                f"{marker[1]}",
                c=colors[index],
                label=f"|2> {label[index]}",
            )

        for index, magnitude in enumerate(self.magnitudes):
            axis.plot(self.fit_independents, self.fit_ys[index], "-", c=colors[index])

        axis.plot(
            [],
            [],
            alpha=0,
            label="Reset Fidelity = {:.3f}".format(self.pop_loss),
            zorder=-10,
        )
        axis.plot(
            [], [], alpha=0, label="Leakage = {:.3f}".format(self.leakage), zorder=-10
        )
        axis.set_xlim([self.independents[0], self.independents[-1]])
        axis.legend(loc="upper right")
        axis.set_ylim(-0.01, 1.01)
        axis.set_xlabel("State")
        axis.set_ylabel("Population")
        axis.set_xticklabels(states)
        axis.set_title(
            f"{name} Calibration - {dh.get_legacy('qubit_types')[self.qubit]} Qubit {self.qubit[1:]}"
        )


class ResetCalibrationSSRONodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = ResetCalibrationSSROQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)


class CZCalibrationSSRONodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = CZCalibrationSSROQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
