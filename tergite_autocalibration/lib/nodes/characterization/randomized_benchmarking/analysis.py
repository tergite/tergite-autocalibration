# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Amr Osman 2024
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Module containing classes that model, fit and plot data from a Rabi experiment.
"""
import lmfit
from scipy.linalg import norm
from scipy.optimize import minimize
from numpy.linalg import inv
from matplotlib import pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import confusion_matrix

from ....base.analysis import BaseAllQubitsRepeatAnalysis, BaseQubitAnalysis
from tergite_autocalibration.lib.utils.functions import (
    exponential_decay_function,
)


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


class ExpDecayModel(lmfit.model.Model):
    """
    Generate an exponential decay model that can be fit to randomized benchmarking data.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(exponential_decay_function, *args, **kwargs)

        self.set_param_hint("A", vary=True)
        self.set_param_hint("B", vary=True, min=0)
        self.set_param_hint("p", vary=True, min=0)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        m = kws.get("m", None)

        if m is None:
            return None

        amplitude_guess = 1 / 2
        self.set_param_hint("A", value=amplitude_guess)

        offset_guess = data[-1]
        self.set_param_hint("B", value=offset_guess)

        p_guess = 0.95
        self.set_param_hint("p", value=p_guess)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)


class RandomizedBenchmarkingSSROQubitAnalysis(BaseQubitAnalysis):
    """
    Analysis that fits an exponential decay function to randomized benchmarking data.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.fit_results = {}

    def analyse_qubit(self):
        for coord in self.dataset[self.data_var].coords:
            if "cliffords" in coord:
                self.number_cliffords_coord = coord
            elif "seed" in coord:
                self.seed_coord = coord
            elif "shot" in str(coord):
                self.shot_coord = coord

        self.independents = np.array(
            [
                float(val)
                for val in self.dataset[self.number_cliffords_coord].values[:-3]
            ]
        )
        self.calibs = self.dataset[self.number_cliffords_coord].values[-3:]

        self.number_of_repetitions = self.dataset.dims[self.seed_coord]
        self.seeds = self.dataset.coords[self.seed_coord]
        self.number_of_cliffords = self.dataset[self.number_cliffords_coord].values
        self.number_of_cliffords_runs = self.dataset.dims[self.number_cliffords_coord]
        self.normalized_data_dict = {}
        self.shots = len(self.dataset[self.shot_coord].values)
        self.fit_results = {}

        self.all_magnitudes = []
        for indx, _ in enumerate(self.seeds):
            # Calculate confusion matrix from calibration shots
            y = np.repeat(self.calibs, self.shots)
            IQ_complex = np.array([])
            for state, _ in enumerate(self.calibs):
                IQ_complex_0 = self.S21[self.data_var].isel(
                    {self.seed_coord: indx, self.number_cliffords_coord: -3 + state}
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
            raw_data = self.S21[self.data_var].isel({self.seed_coord: indx}).values
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
                if len(counts) == 1:
                    counts = np.append(counts, 0)
                    counts = np.append(counts, 0)
                elif len(counts) == 2 and uniques[1] == "c2":
                    pop2 = counts[1]
                    counts[1] = 0
                    counts = np.append(counts, pop2)
                elif len(counts) == 2:
                    counts = np.append(counts, 0)
                raw_prob = counts / len(sweep)
                mitigate_prob = mitigate(raw_prob, cm_inv)
                data_res = np.append(data_res, raw_prob)
            data_res = data_res.reshape(data_res_shape)
            self.all_magnitudes.append(data_res)
        self.all_magnitudes = np.array(self.all_magnitudes)

        # Fitting the 0 state data
        self.magnitudes = self.all_magnitudes[:, :-3, 0]
        self.magnitudes2 = self.all_magnitudes[:, :-3, 2]
        sum = np.sum([arr for arr in self.magnitudes], axis=0)
        self.sum = sum / self.number_of_repetitions

        sum2 = np.sum([arr for arr in self.magnitudes2], axis=0)
        self.sum2 = sum2 / self.number_of_repetitions
        self.number_of_cliffords = [
            int(num_clif) for num_clif in self.number_of_cliffords[:-3]
        ]
        model = ExpDecayModel()

        guess = model.guess(data=self.sum, m=self.number_of_cliffords)
        fit_result = model.fit(self.sum, params=guess, m=self.number_of_cliffords)

        self.fit_n_cliffords = np.linspace(
            self.number_of_cliffords[0], self.number_of_cliffords[-1], 400
        )
        self.fit_y = model.eval(
            fit_result.params, **{model.independent_vars[0]: self.fit_n_cliffords}
        )

        # Gives an initial guess for the model parameters and then fits the model to the data.
        guess2 = model.guess(data=self.sum2, m=self.number_of_cliffords)

        # Adjust the parameters for an inverted decaying exponential fit
        guess2["A"].value = -abs(max(self.sum2))  # Force 'a' to be negative
        guess2["p"].value = 0.998
        fit_result2 = model.fit(self.sum2, params=guess2, m=self.number_of_cliffords)
        self.fit_y2 = model.eval(
            fit_result2.params, **{model.independent_vars[0]: self.fit_n_cliffords}
        )

        fidelities = []
        for trace in self.magnitudes:
            # Gives an initial guess for the model parameters and then fits the model to the data.
            guess = model.guess(data=trace, m=self.number_of_cliffords)
            fit_result = model.fit(trace, params=guess, m=self.number_of_cliffords)
            fidelities.append(fit_result.params["p"].value)

        self.fidelity = np.mean(np.array(fidelities))
        self.fidelity_error = np.std(np.array(fidelities))

        leakage = []
        for trace in self.magnitudes2:
            # Gives an initial guess for the model parameters and then fits the model to the data.
            guess2 = model.guess(data=trace, m=self.number_of_cliffords)

            # Adjust the parameters for an inverted decaying exponential fit
            guess2["A"].value = -abs(max(trace))  # Force 'a' to be negative
            guess2["p"].value = 0.998
            fit_result2 = model.fit(trace, params=guess2, m=self.number_of_cliffords)
            leakage_i = fit_result2.params["p"].value

            leakage_i = 1 - leakage_i
            leakage.append(leakage_i)

        self.leakage = np.mean(np.array(leakage))
        self.leakage_error = np.std(np.array(leakage))

        return self.fidelity, self.fidelity_error, self.leakage, self.leakage_error

    def plotter(self, ax: Axes):
        marker = ["o", "s", "^", "--"]
        x = range(3)
        colors = plt.get_cmap("RdBu_r")(np.linspace(0.2, 0.8, len(x)))

        for index, magnitude in enumerate(self.all_magnitudes):
            if index == 0:
                ax.plot(
                    self.number_of_cliffords,
                    magnitude[:-3, 2],
                    f"{marker[1]}",
                    c="b",
                    label=f"2>",
                    markerfacecolor="none",
                )
                ax.plot(
                    self.number_of_cliffords,
                    magnitude[:-3, 0],
                    f"{marker[0]}",
                    c="b",
                    label=f"0>",
                    markerfacecolor="none",
                )
                ax.plot(
                    self.number_of_cliffords,
                    magnitude[:-3, 1],
                    f"{marker[2]}",
                    c="b",
                    label=f"1>",
                    markerfacecolor="none",
                )
            else:
                ax.plot(
                    self.number_of_cliffords,
                    magnitude[:-3, 2],
                    f"{marker[1]}",
                    c="b",
                    markerfacecolor="none",
                )
                ax.plot(
                    self.number_of_cliffords,
                    magnitude[:-3, 0],
                    f"{marker[0]}",
                    c="b",
                    markerfacecolor="none",
                )
                ax.plot(
                    self.number_of_cliffords,
                    magnitude[:-3, 1],
                    f"{marker[2]}",
                    c="b",
                    markerfacecolor="none",
                )

        ax.plot(
            self.fit_n_cliffords,
            self.fit_y,
            "r--",
            lw=2,
            label=f"p = {self.fidelity:.4f} ± {self.fidelity_error:.4f}",
        )
        ax.plot(
            self.fit_n_cliffords,
            self.fit_y2,
            "k--",
            lw=2,
            label=f"l = {self.leakage:.4f} ± {self.leakage_error:.4f}",
        )

        # Set labels and title
        ax.set_ylabel("population", fontsize=20)
        ax.set_xlabel("number of cliffords", fontsize=20)
        ax.tick_params(axis="both", which="major", labelsize=20)

        # Set y-axis limits to be between 0 and 1
        ax.set_ylim(-0.05, 1.05)
        ax.grid()


class RandomizedBenchmarkingSSRONodeAnalysis(BaseAllQubitsRepeatAnalysis):
    single_qubit_analysis_obj = RandomizedBenchmarkingSSROQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.repeat_coordinate_name = "seeds"
