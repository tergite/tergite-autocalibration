# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023
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

from ....base.analysis import BaseQubitAnalysis, BaseAllQubitsAnalysis


class MotzoiBaseQubitAnalysis(BaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.fit_results = {}
        self.optimal_motzoi = None

    def analyse_qubit(self):
        """
        Analyze the magnitudes to determine the optimal Motzoi parameter.
        """

        # Get the relevant motzoi key from the dataset
        motzoi_key = f"mw_motzois{self.qubit}"
        motzois = self.dataset[motzoi_key].size

        # Calculate the sum of the magnitudes for each motzoi index
        sums = [
            np.sum(self.magnitudes[self.data_var][i].values)
            for i in range(motzois)
        ]

        # Find the index with the minimum sum (optimal motzoi)
        index_of_min = np.argmin(sums)
        self.optimal_motzoi = float(self.magnitudes[motzoi_key][index_of_min].values)

        # Return the optimal motzoi val
        return [self.optimal_motzoi]

    def plotter(self, axis):
        datarray = self.magnitudes[self.data_var]  
        datarray.plot(ax=axis, x=f"mw_motzois{self.qubit}", cmap="RdBu_r")

        # Mark the optimal motzoi on the plot
        axis.axvline(self.optimal_motzoi, c="k", lw=4, linestyle="--", label=f"Optimal Motzoi: {self.optimal_motzoi}")
        axis.legend()

class Motzoi01QubitAnalysis(MotzoiBaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.redis_field = "clock_freqs:f01"


class Motzoi12QubitAnalysis(MotzoiBaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.redis_field = "clock_freqs:f12"


class Motzoi01NodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = Motzoi01QubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)


class Motzoi12NodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = Motzoi12QubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
