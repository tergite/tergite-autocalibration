from tergite_autocalibration.lib.base.analysis import BaseAnalysis


class CZ_Characterisation_Fix_Duration_Analysis(BaseAnalysis):
    def __init__(self) -> None:
        pass

    def run_fitting(self) -> list[float, float]:
        print("WARNING TESTING CZ FREQUeNCY AND AMPLITUDE ANALYSIS")
        return self.run_fitting_find_min()

    def plotter(self, axis):
        pass