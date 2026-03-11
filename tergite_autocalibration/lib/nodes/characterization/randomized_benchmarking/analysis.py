# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024, 2026
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

import numpy as np
from matplotlib.axes import Axes
from scipy.linalg import norm
from scipy.optimize import minimize

from tergite_autocalibration.lib.base.analysis import (
    BaseAllQubitsAnalysis,
    BaseQubitAnalysis,
)
from tergite_autocalibration.lib.utils.analysis_models import ExpDecayModel
from tergite_autocalibration.lib.utils.classification_functions import (
    calculate_probabilities,
)
from tergite_autocalibration.utils.dto.qoi import QOI


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


class RandomizedBenchmarkingSSROQubitAnalysis(BaseQubitAnalysis):
    """
    Analysis that fits an exponential decay function to randomized benchmarking data.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.fit_results = {}

    def analyse_qubit(self):

        model = ExpDecayModel()

        for coord in self.dataset[self.data_var].coords:
            if "cliffords" in coord:
                self.number_cliffords_coord = coord
                self.number_cliffords = self.S21[coord]
            elif "seed" in coord:
                self.seed_coord = coord
                self.seeds = self.S21[coord].values
            elif "loops" in str(coord):
                self.loops_coord = coord
                self.number_of_loops = self.S21[coord].size
            elif "interleave" in str(coord):
                self.interleave_gate_coord = coord
                self.gates = self.S21[coord].values
                self.number_of_gates = self.S21[coord].size
                self.interleaved_gate = None

        if self.number_of_gates == 2:
            self.interleaved_gate = self.gates[1]

        qubit = self.qubit
        iq_array = self.S21[self.data_var].assign_attrs(qubit=qubit)

        self.state_probabilities = calculate_probabilities(iq_array)

        standard_probabilities = self.state_probabilities.sel(
            {self.interleave_gate_coord: "Standard"}
        )
        standard_mean_probabilities_state_0 = standard_probabilities.sel(state=0).mean(
            self.seed_coord
        )
        standard_mean_probabilities_state_1 = standard_probabilities.sel(state=1).mean(
            self.seed_coord
        )
        standard_mean_probabilities_state_2 = standard_probabilities.sel(state=2).mean(
            self.seed_coord
        )

        guess = model.guess(
            data=standard_mean_probabilities_state_0.values,
            m=self.number_cliffords.values,
        )
        fit_result = model.fit(
            standard_mean_probabilities_state_0.values,
            params=guess,
            m=self.number_cliffords.values,
        )

        self.fit_n_cliffords = np.linspace(
            self.number_cliffords.values[0], self.number_cliffords.values[-1], 400
        )
        self.standard_fit_y = model.eval(
            fit_result.params, **{model.independent_vars[0]: self.fit_n_cliffords}
        )
        self.fidelity = fit_result.params["p"].value

        # Gives an initial guess for the model parameters and then fits the model to the data.
        guess2 = model.guess(
            data=standard_mean_probabilities_state_2.values, m=self.number_cliffords
        )

        # Adjust the parameters for an inverted decaying exponential fit
        guess2["A"].value = -1 / 2  # Force 'A' to be negative
        guess2["p"].value = 0.998
        fit_result2 = model.fit(
            standard_mean_probabilities_state_2, params=guess2, m=self.number_cliffords
        )
        self.fit_y2 = model.eval(
            fit_result2.params, **{model.independent_vars[0]: self.fit_n_cliffords}
        )
        self.leakage = 1 - fit_result2.params["p"].value

        if self.interleaved_gate is not None:
            interleaved_probabilities = self.state_probabilities.sel(
                {self.interleave_gate_coord: self.interleaved_gate}
            )
            interleaved_mean_probabilities_state_0 = interleaved_probabilities.sel(
                state=0
            ).mean(self.seed_coord)
            interleaved_mean_probabilities_state_1 = interleaved_probabilities.sel(
                state=1
            ).mean(self.seed_coord)
            interleaved_mean_probabilities_state_2 = interleaved_probabilities.sel(
                state=2
            ).mean(self.seed_coord)

            guess = model.guess(
                data=interleaved_mean_probabilities_state_0.values,
                m=self.number_cliffords.values,
            )
            fit_result = model.fit(
                interleaved_mean_probabilities_state_0.values,
                params=guess,
                m=self.number_cliffords.values,
            )
            self.interleaved_fit_y = model.eval(
                fit_result.params, **{model.independent_vars[0]: self.fit_n_cliffords}
            )
            self.interleaved_fidelity = fit_result.params["p"].value

        analysis_successful = True

        analysis_result = {
            "fidelity": {
                "value": self.fidelity,
                "error": np.nan,
            },
            "leakage": {
                "value": self.leakage,
                "error": np.nan,
            },
        }

        qoi = QOI(analysis_result, analysis_successful)

        return qoi

    def plotter(self, ax: Axes):
        standard_probabilities = self.state_probabilities.sel(
            {self.interleave_gate_coord: "Standard"}
        )

        styles = dict(c="b", lw=0.5)
        standard_probabilities.sel(state=0).plot.line(
            ax=ax, x=self.number_cliffords_coord, **styles
        )
        styles = dict(c="r", lw=0.5)
        standard_probabilities.sel(state=1).plot.line(
            ax=ax, x=self.number_cliffords_coord, **styles
        )
        styles = dict(c="g", lw=0.5)
        standard_probabilities.sel(state=2).plot.line(
            ax=ax, x=self.number_cliffords_coord, **styles
        )
        ax.plot(
            self.fit_n_cliffords,
            self.standard_fit_y,
            "b--",
            lw=2,
            # label=f"p = {self.fidelity:.4f} ± {self.fidelity_error:.4f}",
            label=rf"$p_{{SRB}}$ = {self.fidelity:.4f}",
        )
        ax.plot(
            self.fit_n_cliffords,
            self.fit_y2,
            "g--",
            lw=2,
            label=f"leakage = {self.leakage:.4f}",
        )
        if self.interleaved_gate is not None:
            ax.plot(
                self.fit_n_cliffords,
                self.interleaved_fit_y,
                "c--",
                lw=2,
                label=rf"$p_{{IRB}}$ = {self.interleaved_fidelity:.4f}",
            )
        ax.set_ylabel("population", fontsize=14)
        ax.set_xlabel("number of cliffords", fontsize=14)
        ax.legend()
        ax.tick_params(axis="both", which="major", labelsize=14)
        ax.set_title("")
        ax.grid()


class RandomizedBenchmarkingNodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = RandomizedBenchmarkingSSROQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
