# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2024
# (C) Copyright Eleftherios Moschandreou 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


from tergite_autocalibration.lib.base.analysis import (
    BaseAllQubitsAnalysis,
    BaseQubitAnalysis,
)


class ResonatorRelaxationAnalysis(BaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def analyse_qubit(self):
        for coord in self.dataset[self.data_var].coords:
            if "frequencies" in coord:
                self.frequencies = coord
            elif "durations" in coord:
                self.durations = coord
        return [0]

    def plotter(self, ax):
        self.magnitudes[self.data_var].plot(ax=ax, x=self.frequencies)


class ResonatorRelaxationNodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = ResonatorRelaxationAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
