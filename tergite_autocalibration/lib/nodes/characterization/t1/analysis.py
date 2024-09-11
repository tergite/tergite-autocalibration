# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Amr Osman 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Module containing a class that fits and plots data from a T1 experiment.
"""

import numpy as np
import xarray as xr
from quantify_core.analysis.fitting_models import ExpDecayModel

from ....base.analysis import BaseAnalysis


class T1Analysis(BaseAnalysis):
    """
    Analysis that fits an exponential decay function to obtain
    the T1 relaxation time from experiment data.
    """

    def __init__(self, dataset: xr.Dataset):
        super().__init__()
        self.dataset = dataset
        self.data_var = list(dataset.data_vars.keys())[0]
        for coord in dataset[self.data_var].coords:
            if "repeat" in coord:
                self.repeat_coord = coord
            elif "delays" in coord:
                self.delays_coord = coord
        self.S21 = dataset[self.data_var].values
        self.delays = dataset[self.delays_coord].values

        self.fit_results = {}
        self.qubit = dataset[self.data_var].attrs["qubit"]

    def run_fitting(self):
        model = ExpDecayModel()

        delays = self.delays
        self.fit_delays = np.linspace(
            delays[0], delays[-1], 400
        )  # x-values for plotting
        self.T1_times = []
        for indx, repeat in enumerate(self.dataset.coords[self.repeat_coord]):
            complex_values = self.dataset[self.data_var].isel(
                {self.repeat_coord: [indx]}
            )
            magnitudes = np.array(np.absolute(complex_values.values).flat)

            # Gives an initial guess for the model parameters and then fits the model to the data.
            guess = model.guess(data=magnitudes, delay=delays)
            fit_result = model.fit(magnitudes, params=guess, t=delays)
            self.fit_y = model.eval(
                fit_result.params, **{model.independent_vars[0]: self.fit_delays}
            )
            self.T1_times.append(fit_result.params["tau"].value)
        self.average_T1 = np.mean(self.T1_times)
        self.error = np.std(self.T1_times)
        return [self.average_T1]

    def plotter(self, ax):
        for indx, repeat in enumerate(self.dataset.coords[self.repeat_coord]):
            complex_values = self.dataset[self.data_var].isel(
                {self.repeat_coord: [indx]}
            )
            magnitudes = np.array(np.absolute(complex_values.values).flat)
            ax.plot(self.delays, magnitudes)
        # ax.plot( self.fit_delays , self.fit_y,'r-', lw=3.0, label=f'T1 = {self.T1_time * 1e6:.1f} μs')
        # ax.plot(self.independents, self.magnitudes,'bo-',ms=3.0)
        ax.plot(
            self.fit_delays,
            self.fit_y,
            "r--",
            label=f"Mean T1 = {self.average_T1 * 1e6:.1f} ± {self.error * 1e6:.1f} μs",
        )
        ax.set_title(f"T1 experiment for {self.qubit}")
        ax.set_xlabel("Delay (s)")
        ax.set_ylabel("|S21| (V)")

        ax.grid()


def cos_func(
    x: float,
    frequency: float,
    amplitude: float,
    offset: float,
    x0: float,
    phase: float = 0,
) -> float:
    return (
        amplitude * np.cos(2 * np.pi * frequency * (x + phase)) * np.exp(-x / x0)
        + offset
    )
