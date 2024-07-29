import numpy as np
import xarray as xr

class CZ_Parametrisation_Combined_Frequency_vs_Amplitude_Analysis():
    def __init__(self, res1: list[float], res2: list[float]):
        super().__init__()
        self.result_q1 = res1
        self.result_q2 = res2
        self.frequency_tollerance = 2.5e6 # Hz
        self.amplitude_tollerance = 0.06

    def are_two_qubits_compatible(self):
        return self.are_frequencies_compatible() and self.are_amplitudes_compatible()
    
    def are_frequencies_compatible(self):
        return abs(self.result_q1[0]-self.result_q2[0]) < self.frequency_tollerance
    
    def are_amplitudes_compatible(self):
        return abs(self.result_q1[1]-self.result_q2[1]) < self.amplitude_tollerance