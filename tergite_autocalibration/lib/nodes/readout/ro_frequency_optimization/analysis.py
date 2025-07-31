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
from tergite_autocalibration.utils.dto.qoi import QOI

model = fm.ResonatorModel()


class OptimalRO01FrequencyQubitAnalysis(BaseQubitAnalysis):
    """
    Analysis that fits the data of resonator spectroscopy experiments
    and extractst the optimal RO frequency.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def analyse_qubit(self):
        for coord in self.dataset.coords:
            if "frequencies" in str(coord):
                self.frequencies = self.dataset[coord].values
                self.frequency_coord = coord
            elif "qubit_states" in str(coord):
                self.qubit_states = self.dataset[coord].values
                self.qubit_state_coord = coord

        self.s21_0 = self.S21[self.data_var].sel({self.qubit_state_coord: 0})
        self.s21_1 = self.S21[self.data_var].sel({self.qubit_state_coord: 1})
        self.magnitudes_0 = np.abs(self.s21_0)
        self.magnitudes_1 = np.abs(self.s21_1)
        self.phase_0 = np.angle(self.s21_0)
        self.phase_1 = np.angle(self.s21_1)

        distances = self.s21_1 - self.s21_0

        self.optimal_frequency = np.abs(distances).idxmax().item()
        self.index_of_max_distance = np.abs(distances).argmax()

        analysis_successful = True
        analysis_result = {
            "extended_clock_freqs:readout_2state_opt": {
                "value": self.optimal_frequency,
                "error": 0,
            }
        }

        qoi = QOI(analysis_result, analysis_successful)

        return qoi

    def plotter(self, ax, secondary_axes):
        """
        primary axis: the |0> and |1> resonator traces on the IQ plane.
            The points for which the distance between the traces is maximized is denoted.
        magnitude_axis: s21 magnitudes in terms of the frequency for both
            the |0> and |1> resonator traces. Optimal frequency is denoted.
        phase_axis: s21 phases in terms of the frequency for both
            the |0> and |1> resonator traces. Optimal frequency is denoted.
        """

        ro_freq = float(
            REDIS_CONNECTION.hget(f"transmons:{self.qubit}", "clock_freqs:readout")
        )
        ro_freq_1 = float(
            REDIS_CONNECTION.hget(
                f"transmons:{self.qubit}", "extended_clock_freqs:readout_1"
            )
        )
        ax.set_xlabel("I quadrature (V)")
        ax.set_ylabel("Q quadrature (V)")

        f0 = self.s21_0[self.index_of_max_distance]
        f1 = self.s21_1[self.index_of_max_distance]
        label_text = f"opt_ro: {int(self.optimal_frequency)}\n"
        label_text += f"|0>_ro: {int(ro_freq)}\n"
        label_text += f"|1>_ro: {int(ro_freq_1)}"
        ax.scatter(
            [f0.real, f1.real],
            [f0.imag, f1.imag],
            marker="*",
            c="black",
            s=124,
            label=label_text,
            zorder=5,
        )

        ax.plot(self.s21_0.real, self.s21_0.imag, "bo-", lw=2, ms=4)
        ax.plot(self.s21_1.real, self.s21_1.imag, "ro-", lw=2, ms=4)

        ax.legend()
        ax.grid()

        magnitude_axis = secondary_axes[0]
        phase_axis = secondary_axes[1]
        magnitude_axis.plot(
            self.frequencies, self.magnitudes_0, "o-", ms=2, color="blue"
        )
        magnitude_axis.plot(
            self.frequencies, self.magnitudes_1, "o-", ms=2, color="red"
        )
        magnitude_axis.axvline(self.optimal_frequency, color="black")
        phase_axis.plot(self.frequencies, self.phase_0, "o-", ms=2, color="blue")
        phase_axis.plot(self.frequencies, self.phase_1, "o-", ms=2, color="red")
        phase_axis.axvline(self.optimal_frequency, color="black")


class OptimalRO012FrequencyQubitAnalysis(OptimalRO01FrequencyQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def analyse_qubit(self):
        super().analyse_qubit()
        self.s21_2 = self.S21[self.data_var].sel({self.qubit_state_coord: 2})
        self.magnitudes_2 = np.abs(self.s21_2)

        re_0 = self.s21_0.real
        im_0 = self.s21_0.imag
        re_1 = self.s21_1.real
        im_1 = self.s21_1.imag
        re_2 = self.s21_2.real
        im_2 = self.s21_2.imag
        distances_01 = np.sqrt((re_0 - re_1) ** 2 + (im_0 - im_1) ** 2)
        distances_12 = np.sqrt((re_1 - re_2) ** 2 + (im_1 - im_2) ** 2)
        distances_20 = np.sqrt((re_2 - re_0) ** 2 + (im_2 - im_0) ** 2)

        # following Heron's formula for the maximum area of the triangle
        s = (distances_01 + distances_12 + distances_20) / 2
        self.area = np.sqrt(
            s * (s - distances_01) * (s - distances_12) * (s - distances_20)
        )

        self.optimal_frequency = self.area.idxmax().item()
        self.optimal_distance = self.area.max().item()

        analysis_successful = True
        analysis_result = {
            "extended_clock_freqs:readout_3state_opt": {
                "value": self.optimal_frequency,
                "error": 0,
            }
        }

        qoi = QOI(analysis_result, analysis_successful)

        return qoi

    def plotter(self, ax):
        ax.set_xlabel("RO frequency")
        ax.set_ylabel("IQ distance")
        ax.plot(self.frequencies, np.abs(self.magnitudes_0), label="0")
        ax.plot(self.frequencies, np.abs(self.magnitudes_1), label="1")
        ax.plot(self.frequencies, np.abs(self.magnitudes_2), label="2")
        ax.plot(
            self.frequencies, self.area * 1.5e2, "--", label="area"
        )  # *2e2 for visibility in plot

        ax.scatter(
            self.optimal_frequency,
            self.optimal_distance * 1.5e2,  # factor for visibility in plot
            marker="*",
            c="red",
            s=64,
        )
        ax.grid()


class OptimalRO01FrequencyNodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = OptimalRO01FrequencyQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.plots_per_qubit = 3

    def _fill_plots(self):
        for index, analysis in enumerate(self.qubit_analyses):
            primary_plot_row = self.plots_per_qubit * (index // self.column_grid)
            primary_axis = self.axs[primary_plot_row, index % self.column_grid]

            list_of_secondary_axes = []
            for plot_indx in range(1, self.plots_per_qubit):
                secondary_plot_row = primary_plot_row + plot_indx
                list_of_secondary_axes.append(
                    self.axs[secondary_plot_row, index % self.column_grid]
                )

            analysis.plotter(primary_axis, list_of_secondary_axes)


class OptimalRO012FrequencyNodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = OptimalRO012FrequencyQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
