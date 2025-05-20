# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023
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


class PunchoutAnalysis(BaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def analyse_qubit(self):
        for coord in self.dataset[self.data_var].coords:
            if "frequencies" in coord:
                self.frequencies = coord
            elif "amplitudes" in coord:
                self.amplitudes = coord
        self.dataset[f"y{self.qubit}"].values = np.abs(
            self.dataset[f"y{self.qubit}"].values
        )
        magnitudes = self.magnitudes[self.data_var].values
        norm_magnitudes = magnitudes / np.max(magnitudes, axis=0)
        self.S21[f"y{self.qubit}"].values = norm_magnitudes

        analysis_successful = False

        analysis_result = {
            "punchout": {
                "value": np.nan,
                "error": np.nan,
            }
        }

        qoi = QOI(analysis_result, analysis_successful)

        return qoi

    def plotter(self, ax):
        self.S21[self.data_var].plot(ax=ax, x=self.frequencies, yscale="log")


class PunchoutNodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = PunchoutAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
