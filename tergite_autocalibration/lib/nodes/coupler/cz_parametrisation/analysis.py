from tergite_autocalibration.lib.base.analysis import BaseAnalysis
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation import (
    CZ_Parametrisation_Combined_Frequency_vs_Amplitude_Analysis,
)
from typing import List, Tuple

from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.utils import (
    NoValidCombinationException,
)


class CZ_Parametrisation_Fix_Duration_Analysis(BaseAnalysis):
    def __init__(self) -> None:
        self.opt_freq = -1
        self.opt_amp = -1
        self.opt_current = -1
        pass

    def run_fitting(self) -> list[float, float]:
        print("WARNING TESTING CZ FREQUeNCY AND AMPLITUDE ANALYSIS")
        return self.run_analysis_on_freq_amp_results()

    def run_analysis_on_freq_amp_results(
        self,
        results: List[
            Tuple[CZ_Parametrisation_Combined_Frequency_vs_Amplitude_Analysis, float]
        ],
    ):
        minCurrent = 1
        bestIndex = -1
        for index, result in enumerate(results):
            if result[0].are_two_qubits_compatible() and result[1] < minCurrent:
                minCurrent = result[1]
                bestIndex = index

        if bestIndex == -1:
            raise NoValidCombinationException

        self.opt_index = bestIndex
        self.opt_freq = results[bestIndex][0].best_parameters()[0]
        self.opt_amp = results[bestIndex][0].best_parameters()[1]
        self.opt_current = minCurrent

    def plotter(self, axis):
        pass
