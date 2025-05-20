# This code is part of Tergite
#
# (C) Copyright Liangyu Chen 2024
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
from abc import ABC
from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt
from numpy.linalg import inv
from scipy.linalg import norm
from scipy.optimize import minimize
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import confusion_matrix

from tergite_autocalibration.config.legacy import dh
from tergite_autocalibration.lib.base.analysis import (
    BaseAllQubitsAnalysis,
    BaseQubitAnalysis,
)
from tergite_autocalibration.utils.logging import logger


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


class ProcessTomographyQubitAnalysis(BaseQubitAnalysis):
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

            confusion_matrix(y, y_pred)
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

                mitigate_prob = mitigate(raw_prob, cm_inv)
                data_res = np.append(data_res, mitigate_prob)
            data_res = data_res.reshape(data_res_shape)
            self.all_magnitudes.append(data_res)
        self.all_magnitudes = np.array(self.all_magnitudes)
        # Fitting the 1 state data
        self.g_magnitudes = self.all_magnitudes[:, :-3, 0]
        self.e_magnitudes = self.all_magnitudes[:, :-3, 1]
        self.f_magnitudes = self.all_magnitudes[:, :-3, 2]

        g_magnitudes_str = ",".join(
            str(element) for element in list(self.g_magnitudes.flatten())
        )

        e_magnitudes_str = ",".join(
            str(element) for element in list(self.e_magnitudes.flatten())
        )
        f_magnitudes_str = ",".join(
            str(element) for element in list(self.f_magnitudes.flatten())
        )

        logger.debug(f"{self.g_magnitudes = }")
        logger.debug(f"{self.e_magnitudes = }")
        logger.debug(f"{self.f_magnitudes = }")
        return [g_magnitudes_str, e_magnitudes_str, f_magnitudes_str]

    def plotter(self, axis):
        state = ["0", "1", "2"]
        states = list(itertools.product(state, state))
        states = [state[0] + state[1] for state in states]

        label = ["Reset Off", "Reset On"]
        name = "Reset"
        x = range(len(label))
        marker = [".", "*", "v", "s"]
        colors = plt.get_cmap("RdBu_r")(np.linspace(0.2, 0.8, len(x)))

        for index, magnitude in enumerate(self.all_magnitudes):
            axis.plot(
                self.independents,
                magnitude[:-3, 0],
                f"{marker[0]}",
            )

            axis.plot(
                self.independents,
                magnitude[:-3, 1],
                f"{marker[1]}",
            )
            axis.plot(
                self.independents,
                magnitude[:-3, 2],
                f"{marker[2]}",
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

    def save_plot(self):
        self.fig.tight_layout()
        preview_path = self.data_path / f"{self.name}_preview.png"
        full_path = self.data_path / f"{self.name}.png"
        self.fig.savefig(preview_path, bbox_inches="tight", dpi=100)
        self.fig.savefig(full_path, bbox_inches="tight", dpi=400)
        plt.show(block=False)
        plt.pause(5)
        plt.close()
        logger.info(f"Plots saved to {preview_path} and {full_path}")


class SingleProcessTomographyNodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = ProcessTomographyQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)


class ProcessTomographyNodeAnalysis(BaseAllQubitsAnalysis, ABC):
    node_analysis_obj = SingleProcessTomographyNodeAnalysis

    def __init__(self, name: str, redis_fields):
        super().__init__(name, redis_fields)
        self.loop_range = range(9)

    def analyze_node(self, data_path: Path):
        for i in self.loop_range:
            qubit_analysis = self.node_analysis_obj(self.name, self.redis_fields)
            qubit_analysis.analyze_node(data_path, i)
        # Note: The process tomography analysis neither returns a value nor saves a value to redis
