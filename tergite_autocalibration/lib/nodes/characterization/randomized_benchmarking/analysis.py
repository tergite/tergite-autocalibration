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

import numpy as np
import xarray as xr
from matplotlib.axes import Axes
from scipy.linalg import norm
from scipy.optimize import minimize

from tergite_autocalibration.lib.base.analysis import (
<<<<<<< HEAD
    BaseAllQubitsAnalysis,
    BaseQubitAnalysis,
)
from tergite_autocalibration.lib.base.analysis_models import ExpDecayModel
from tergite_autocalibration.lib.base.classification_functions import assign_state
=======
    BaseAllQubitsRepeatAnalysis,
    BaseQubitAnalysis,
)
from tergite_autocalibration.lib.utils.analysis_models import ExpDecayModel
from tergite_autocalibration.lib.utils.classification_functions import assign_state
>>>>>>> eleftherios/fix/fix-ro-amplitude-optimizations


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
        for coord in self.dataset[self.data_var].coords:
            if "cliffords" in coord:
                self.number_cliffords_coord = coord
                self.number_cliffords = self.S21[coord]
            elif "seed" in coord:
                self.seed_coord = coord
                self.seeds = self.S21[coord].values
            elif "loops" in str(coord):
                self.loops_coord = coord
                self.number_of_loops = self.S21[self.loops_coord].size

        qubit = self.qubit

        states_array = assign_state(qubit, self.S21[self.data_var])

        # filter S21 to produce 3 distict datarrays,
        # each with 1 at the position where the classification is True
        # and 0 at the position where the classification is False
        # eg states_array = [0,0,1,1,0,2] ->
        # zeros =[1,1,0,0,1,0]
        # ones = [0,0,1,1,0,0]
        # twos = [0,0,0,0,0,1]
        # probably there is a better way to extract the probabilities
        zeros = xr.where(states_array == 0, x=1, y=0)  # keep only |0> states
        ones = xr.where(states_array == 1, x=1, y=0)  # keep only |1> states
        twos = xr.where(states_array == 2, x=1, y=0)  # keep only |2> states

        # sum the filtered arrays, to get the occurancies of each state
        # when later we divide with the total number, this becomes a probabilities array
        zeros = zeros.reduce(func=np.sum, dim=self.loops_coord)
        ones = ones.reduce(func=np.sum, dim=self.loops_coord)
        twos = twos.reduce(func=np.sum, dim=self.loops_coord)

        probabilities_state_0 = zeros / self.number_of_loops
        self.probabilities_state_0 = probabilities_state_0.assign_coords(state=0)
        probabilities_state_1 = ones / self.number_of_loops
        self.probabilities_state_1 = probabilities_state_1.assign_coords(state=1)
        probabilities_state_2 = twos / self.number_of_loops
        self.probabilities_state_2 = probabilities_state_2.assign_coords(state=2)

        self.mean_probabilities_state_0 = probabilities_state_0.mean(self.seed_coord)
        self.mean_probabilities_state_1 = probabilities_state_1.mean(self.seed_coord)
        self.mean_probabilities_state_2 = probabilities_state_2.mean(self.seed_coord)

        self.state_probabilities = xr.concat(
            [probabilities_state_0, probabilities_state_1, probabilities_state_2],
            dim="state",
        )

        model = ExpDecayModel()

        guess = model.guess(
            data=self.mean_probabilities_state_0.values, m=self.number_cliffords.values
        )
        fit_result = model.fit(
            self.mean_probabilities_state_0.values,
            params=guess,
            m=self.number_cliffords.values,
        )

        self.fit_n_cliffords = np.linspace(
            self.number_cliffords.values[0], self.number_cliffords.values[-1], 400
        )
        self.fit_y = model.eval(
            fit_result.params, **{model.independent_vars[0]: self.fit_n_cliffords}
        )
        self.fidelity = fit_result.params["p"].value

        # Gives an initial guess for the model parameters and then fits the model to the data.
        guess2 = model.guess(
            data=self.mean_probabilities_state_2.values, m=self.number_cliffords
        )

        # Adjust the parameters for an inverted decaying exponential fit
        guess2["A"].value = -1 / 2  # Force 'A' to be negative
        guess2["p"].value = 0.998
        fit_result2 = model.fit(
            self.mean_probabilities_state_2, params=guess2, m=self.number_cliffords
        )
        self.fit_y2 = model.eval(
            fit_result2.params, **{model.independent_vars[0]: self.fit_n_cliffords}
        )
        self.leakage = 1 - fit_result2.params["p"].value

        return self.fidelity, 0, self.leakage, 0

    def plotter(self, ax: Axes):
        for seed in self.seeds:
            self.probabilities_state_0.sel({self.seed_coord: seed}).plot(
                ax=ax,
                c="b",
                marker="o",
                ms=0.5,
                lw=0.5,
                # label="|0>",
            )
            self.probabilities_state_1.sel({self.seed_coord: seed}).plot(
                ax=ax,
                c="r",
                marker="s",
                ms=0.5,
                lw=0.5,
                # label="|1>",
            )
            self.probabilities_state_2.sel({self.seed_coord: seed}).plot(
                ax=ax,
                c="g",
                marker="^",
                ms=0.5,
                lw=0.5,
                # label="|2>",
            )
        ax.plot(
            self.fit_n_cliffords,
            self.fit_y,
            "b--",
            lw=2,
            # label=f"p = {self.fidelity:.4f} ± {self.fidelity_error:.4f}",
            label=f"fidelity = {self.fidelity:.4f}",
        )
        ax.plot(
            self.fit_n_cliffords,
            self.fit_y2,
            "g--",
            lw=2,
            label=f"leakage = {self.leakage:.4f}",
        )
        ax.set_ylabel("population", fontsize=14)
        ax.set_xlabel("number of cliffords", fontsize=14)
        ax.tick_params(axis="both", which="major", labelsize=14)
        ax.set_title("")
        ax.grid()


class RandomizedBenchmarkingSSRONodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = RandomizedBenchmarkingSSROQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
