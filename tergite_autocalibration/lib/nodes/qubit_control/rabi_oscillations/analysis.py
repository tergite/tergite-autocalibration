# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
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
import numpy as np

from tergite_autocalibration.lib.base.analysis import (
    BaseAllQubitsAnalysis,
    BaseQubitAnalysis,
)
from tergite_autocalibration.lib.utils.analysis_models import RabiModel
from tergite_autocalibration.utils.backend.redis_utils import fetch_redis_params
from tergite_autocalibration.utils.dto.qoi import QOI


class RabiQubitAnalysis(BaseQubitAnalysis):
    """
    Analysis that fits a cosine function to Rabi oscillation data.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def _analyse_rabi(self):
        model = RabiModel()

        for coord in self.dataset.coords:
            if "amplitudes" in coord:
                self.amplitude_coord = coord
                self.amplitudes = self.dataset[coord].values
            else:
                raise ValueError("Invalid Coordinate")

        self.fit_plot_amplitudes = np.linspace(
            self.amplitudes[0], self.amplitudes[-1], 400
        )  # x-values for plotting

        # Gives an initial guess for the model parameters and then fits the model to the data.
        guess = model.guess(
            self.magnitudes[self.data_var].values, drive_amp=self.amplitudes
        )
        fit_result = model.fit(
            self.magnitudes[self.data_var].values,
            params=guess,
            drive_amp=self.amplitudes,
        )

        self.pi_amplitude = fit_result.params["amp180"].value
        self.uncertainty = fit_result.params["amp180"].stderr
        self.scaled_uncertainty = self.uncertainty / self.pi_amplitude

        self.fit_y = model.eval(fit_result.params, drive_amp=self.fit_plot_amplitudes)
        return

    def analyse_qubit(self):
        self._analyse_rabi()
        if self.scaled_uncertainty < 2e-2 and self.pi_amplitude < 0.95:
            analysis_successful = True
        else:
            analysis_successful = False

        analysis_result = {
            "rxy:amp180": {
                "value": self.pi_amplitude,
                "error": self.scaled_uncertainty,
            }
        }

        qoi = QOI(analysis_result, analysis_successful)

        return qoi

    def plotter(self, ax):
        ax.plot(
            self.fit_plot_amplitudes,
            self.fit_y,
            "r-",
            lw=3.0,
            label=f"π_ampl = {self.pi_amplitude:.2E}"
            r"$\pm$"
            f"{self.uncertainty:.2E}(V)\n"
            f"scaled uncertainty: {self.scaled_uncertainty:.2E}",
        )

        ax.plot(self.amplitudes, self.magnitudes[self.data_var].values, "bo-", ms=3.0)
        ax.set_title(f"Rabi Oscillations for {self.qubit}")
        ax.set_xlabel("Amplitude (V)")
        ax.set_ylabel("|S21| (V)")
        ax.grid()


class Rabi12QubitAnalysis(RabiQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def analyse_qubit(self):
        self._analyse_rabi()
        if self.scaled_uncertainty < 2e-2 and self.pi_amplitude < 0.95:
            analysis_successful = True
        else:
            analysis_successful = False

        analysis_result = {
            "r12:ef_amp180": {
                "value": self.pi_amplitude,
                "error": self.scaled_uncertainty,
            }
        }

        qoi = QOI(analysis_result, analysis_successful)

        return qoi


class RabiNodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = RabiQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)


class RabiNode12Analysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = Rabi12QubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)


class NRabiQubitAnalysis(BaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def _analyse_n_rabi(self):
        for coord in self.dataset[self.data_var].coords:
            if "amplitudes" in coord:
                self.mw_amplitudes_coord = coord
            elif "repetitions" in coord:
                self.x_repetitions_coord = coord

        mw_amplitude_key = self.mw_amplitudes_coord
        mw_amplitudes = self.magnitudes[mw_amplitude_key].size
        sums = []
        for this_amplitude_index in range(mw_amplitudes):
            this_sum = sum(self.magnitudes[self.data_var][this_amplitude_index].values)
            sums.append(this_sum)

        index_of_min = np.argmin(np.array(sums))
        self.previous_amplitude = fetch_redis_params("rxy:amp180", self.qubit)
        self.optimal_amp180 = (
            self.magnitudes[mw_amplitude_key][index_of_min].values.item()
            + self.previous_amplitude
        )
        self.index_of_max = index_of_min
        self.shift = self.magnitudes[mw_amplitude_key][index_of_min].values

    def analyse_qubit(self):
        self._analyse_n_rabi()
        analysis_successful = True

        analysis_result = {
            "rxy:amp180": {
                "value": self.optimal_amp180,
                "error": 0,
            }
        }

        qoi = QOI(analysis_result, analysis_successful)

        return qoi

    def plotter(self, axis):
        datarray = self.magnitudes[self.data_var]

        datarray.plot(ax=axis, x=f"mw_amplitudes_sweep{self.qubit}", cmap="RdBu_r")
        axis.set_xlabel("mw amplitude correction")
        line = self.shift

        axis.axvline(
            line,
            c="k",
            lw=4,
            linestyle="--",
        )


class NRabi_12_QubitAnalysis(NRabiQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.redis_field = "r12:ef_amp180"

    def analyse_qubit(self):
        self._analyse_n_rabi()

        analysis_successful = True
        analysis_result = {
            self.redis_field: {
                "value": self.optimal_amp180,
                "error": 0,
            }
        }

        qoi = QOI(analysis_result, analysis_successful)

        return qoi


class NRabiNodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = NRabiQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)


class NRabi_12_NodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = NRabi_12_QubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
