# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
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
Module containing a class that fits data from a resonator spectroscopy experiment.
"""
import numpy as np
from quantify_core.analysis import fitting_models as fm

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.lib.base.analysis import (
    BaseAllQubitsAnalysis,
    BaseQubitAnalysis,
)

model = fm.ResonatorModel()


class OptimalRO01FrequencyQubitAnalysis(BaseQubitAnalysis):
    """
    Analysis that fits the data of resonator spectroscopy experiments
    and extractst the optimal RO frequency.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.fit_results = {}
        self.magnitudes_0 = []
        self.magnitudes_1 = []
        self.qubit_state_coord = ""

    def analyse_qubit(self):
        for coord in self.dataset.coords:
            if "frequencies" in str(coord):
                self.frequencies = self.dataset[coord].values
                self.frequency_coord = coord
            elif "qubit_states" in str(coord):
                self.qubit_states = self.dataset[coord].values
                self.qubit_state_coord = coord

        self.magnitudes_0 = (
            self.magnitudes[self.data_var]
            .isel({self.qubit_state_coord: [0]})
            .values.flatten()
        )  # S21 when qubit at |0>
        self.magnitudes_1 = (
            self.magnitudes[self.data_var]
            .isel({self.qubit_state_coord: [1]})
            .values.flatten()
        )  # S21 when qubit at |1>

        # Gives an initial guess for the model parameters and then fits the model to the data.
        guess_0 = model.guess(self.magnitudes_0, f=self.frequencies)
        guess_1 = model.guess(self.magnitudes_1, f=self.frequencies)
        fit_frequencies = np.linspace(self.frequencies[0], self.frequencies[-1], 400)
        self.fit_result_0 = model.fit(
            self.magnitudes_0, params=guess_0, f=self.frequencies
        )
        self.fit_result_1 = model.fit(
            self.magnitudes_1, params=guess_1, f=self.frequencies
        )
        self.fit_IQ_0 = model.eval(self.fit_result_0.params, f=fit_frequencies)
        self.fit_IQ_1 = model.eval(self.fit_result_1.params, f=fit_frequencies)

        fit_values_0 = self.fit_result_0.values
        fit_values_1 = self.fit_result_1.values

        distances = self.fit_IQ_1 - self.fit_IQ_0
        self.index_of_max_distance = np.argmax(np.abs(distances))
        self.optimal_frequency = fit_frequencies[self.index_of_max_distance]

        return [self.optimal_frequency]

    def plotter(self, ax):
        ax.set_xlabel("I quadrature (V)")
        ax.set_ylabel("Q quadrature (V)")
        ax.plot(self.fit_IQ_0.real, self.fit_IQ_0.imag)
        ax.plot(self.fit_IQ_1.real, self.fit_IQ_1.imag)
        f0 = self.fit_IQ_0[self.index_of_max_distance]
        f1 = self.fit_IQ_1[self.index_of_max_distance]

        ro_freq = float(
            REDIS_CONNECTION.hget(f"transmons:{self.qubit}", "clock_freqs:readout")
        )
        ro_freq_1 = float(
            REDIS_CONNECTION.hget(
                f"transmons:{self.qubit}", "extended_clock_freqs:readout_1"
            )
        )

        label_text = f"opt_ro: {int(self.optimal_frequency)}\n"
        label_text += f"|0>_ro: {int(ro_freq)}\n"
        label_text += f"|1>_ro: {int(ro_freq_1)}"

        ax.scatter(
            [f0.real, f1.real],
            [f0.imag, f1.imag],
            marker="*",
            c="red",
            s=64,
            label=label_text,
        )
        ax.grid()


class OptimalRO012FrequencyQubitAnalysis(OptimalRO01FrequencyQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.fit_results = {}
        self.magnitudes_1 = []

    def analyse_qubit(self):
        super().analyse_qubit()
        self.magnitudes_2 = (
            self.magnitudes[self.data_var]
            .isel({self.qubit_state_coord: [2]})
            .values.flatten()
        )  # S21 when qubit at |2>

        guess_2 = model.guess(self.magnitudes_2, f=self.frequencies)
        self.fit_frequencies = np.linspace(
            self.frequencies[0], self.frequencies[-1], 400
        )

        self.fit_result_2 = model.fit(
            self.magnitudes_2, params=guess_2, f=self.frequencies
        )
        self.fit_IQ_2 = model.eval(self.fit_result_2.params, f=self.fit_frequencies)

        fit_values_2 = self.fit_result_2.values

        self.distances_01 = np.abs(self.magnitudes_0 - self.magnitudes_1)
        self.distances_12 = np.abs(self.magnitudes_1 - self.magnitudes_2)
        self.distances_20 = np.abs(self.magnitudes_2 - self.magnitudes_0)
        self.total_distance = (
            self.distances_01 + self.distances_12 + self.distances_20
        ) / 3
        self.index_of_max_distance = np.argmax(self.total_distance)
        self.optimal_frequency = self.frequencies[self.index_of_max_distance]

        return [self.optimal_frequency]

    def plotter(self, ax):
        ax.set_xlabel("RO frequency")
        ax.set_ylabel("IQ distance")
        ax.plot(self.frequencies, np.abs(self.magnitudes_0), label="0")
        ax.plot(self.frequencies, np.abs(self.magnitudes_1), label="1")
        ax.plot(self.frequencies, np.abs(self.magnitudes_2), label="2")
        ax.plot(self.frequencies, self.total_distance, "--", label="distance")
        optimal_distance = self.total_distance[self.index_of_max_distance]

        ax.scatter(
            self.optimal_frequency,
            optimal_distance,
            marker="*",
            c="red",
            s=64,
        )
        ax.grid()


class OptimalRO01FrequencyNodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = OptimalRO01FrequencyQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)


class OptimalRO012FrequencyNodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = OptimalRO012FrequencyQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
