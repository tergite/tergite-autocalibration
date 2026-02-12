# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2025
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

from tergite_autocalibration.lib.base.analysis import (
    BaseAllQubitsAnalysis,
    BaseQubitAnalysis,
)
from tergite_autocalibration.utils.dto.qoi import QOI


class MotzoiBaseQubitAnalysis(BaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.fit_results = {}
        self.optimal_motzoi = None

    def _analyse_motzoi(self):
        """
        Analyze the magnitudes to determine the optimal Motzoi parameter.
        """

        for coord in self.magnitudes.coords:
            coord = str(coord)
            if "motzois" in coord:
                self.motzois_coord = coord
            elif "repetitions" in coord:
                self.x_repetitions_coord = coord

        sums = self.magnitudes.sum(self.x_repetitions_coord)

        self.optimal_motzoi = sums.idxmin()[self.data_var].item()

    def plotter(self, axis):
        datarray = self.magnitudes[self.data_var]
        datarray.plot(ax=axis, x=f"mw_motzois{self.qubit}", cmap="RdBu_r")

        # Mark the optimal motzoi on the plot
        axis.axvline(
            self.optimal_motzoi,
            c="k",
            lw=4,
            linestyle="--",
            label=f"Optimal Motzoi: {self.optimal_motzoi:.3f}",
        )
        axis.legend()


class Motzoi01QubitAnalysis(MotzoiBaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def analyse_qubit(self):
        self._analyse_motzoi()

        analysis_successful = True
        analysis_result = {"rxy:motzoi": {"value": self.optimal_motzoi, "error": 0}}

        qoi = QOI(analysis_result, analysis_successful)

        return qoi


class Motzoi12QubitAnalysis(MotzoiBaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def analyse_qubit(self):
        self._analyse_motzoi()

        analysis_successful = True
        analysis_result = {"r12:ef_motzoi": {"value": self.optimal_motzoi, "error": 0}}

        qoi = QOI(analysis_result, analysis_successful)

        return qoi


class Motzoi01NodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = Motzoi01QubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)


class Motzoi12NodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = Motzoi12QubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
