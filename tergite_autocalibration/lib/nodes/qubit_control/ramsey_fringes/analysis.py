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

import numpy as np

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.lib.base.analysis import (
    BaseAllQubitsAnalysis,
    BaseQubitAnalysis,
)
from tergite_autocalibration.lib.utils.analysis_models import RamseyModel
from tergite_autocalibration.utils.dto.qoi import QOI


class RamseyDetuningsBaseQubitAnalysis(BaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.redis_field = ""

    def analyse_qubit(self):
        for coord in self.dataset.coords:
            if "delay" in coord:
                self.delay_coord = coord
                self.ramsey_delays = self.dataset.coords[coord].values
            elif "detuning" in coord:
                self.detuning_coord = coord
                self.artificial_detunings = self.dataset.coords[coord].values
        redis_key = f"transmons:{self.qubit}"
        redis_value = REDIS_CONNECTION.hget(f"{redis_key}", self.redis_field)
        self.qubit_frequency = float(redis_value)

        model = RamseyModel()
        ramsey_delays = self.dataset.coords[self.delay_coord].values
        self.fit_ramsey_delays = np.linspace(ramsey_delays[0], ramsey_delays[-1], 400)

        fitted_detunings = []
        for indx, detuning in enumerate(self.dataset.coords[self.detuning_coord]):
            magnitudes = (
                self.magnitudes[self.data_var].isel({self.detuning_coord: indx}).values
            )

            # magnitudes = np.array(np.absolute(complex_values.values).flat)
            guess = model.guess(magnitudes, t=ramsey_delays)
            fit_result = model.fit(magnitudes, params=guess, t=ramsey_delays)
            fit_y = model.eval(
                fit_result.params, **{model.independent_vars[0]: self.fit_ramsey_delays}
            )
            fitted_detuning = fit_result.params["frequency"].value
            fitted_detunings.append(fitted_detuning)

        fitted_detunings = np.array(fitted_detunings)

        complex_points = self.artificial_detunings + 1j * fitted_detunings
        directions = np.diff(complex_points)
        angles_of_diffs = np.angle(directions)
        sins_of_diffs = np.abs(np.sin(angles_of_diffs))
        index_of_min = np.argmin(sins_of_diffs) + 1
        self.fitted_detunings = np.concatenate(
            (fitted_detunings[:index_of_min] * (-1), fitted_detunings[index_of_min:])
        )

        m, b = np.polyfit(self.artificial_detunings, self.fitted_detunings, 1)
        self.poly1d_fn = np.poly1d((m, b))
        self.frequency_correction = -b / m

        self.corrected_qubit_frequency = (
            self.qubit_frequency + self.frequency_correction
        )

        analysis_succesful = True

        analysis_result = {
            "clock_freqs:f01": {
                "value": self.corrected_qubit_frequency,
                "error": 0,
            }
        }

        qoi = QOI(analysis_result, analysis_succesful)
        return qoi

    def plotter(self, ax):
        ax.plot(self.artificial_detunings, self.fitted_detunings, "bo", ms=5.0)
        ax.axvline(
            self.frequency_correction,
            color="red",
            label=f"correction: {int(self.frequency_correction) / 1e3} kHz",
        )
        ax.plot(
            self.artificial_detunings,
            self.poly1d_fn(self.artificial_detunings),
            "--b",
            lw=1,
        )
        ax.axvline(0, color="black", lw=1)
        ax.set_xlabel("Artificial detuning (Hz)")
        ax.set_ylabel("Fitted detuning (Hz)")

        ax.grid()


class RamseyDetunings01QubitAnalysis(RamseyDetuningsBaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.redis_field = "clock_freqs:f01"


class RamseyDetunings12QubitAnalysis(RamseyDetuningsBaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.redis_field = "clock_freqs:f12"


class RamseyDetunings01NodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = RamseyDetunings01QubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)


class RamseyDetunings12NodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = RamseyDetunings12QubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
