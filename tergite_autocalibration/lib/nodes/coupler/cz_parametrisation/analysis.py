from matplotlib import pyplot as plt
import numpy as np
import xarray as xr
from typing import List, Tuple

from ....base.analysis import BaseAnalysis

from .utils.no_valid_combination_exception import (
    NoValidCombinationException,
)

class CombinedFrequencyVsAmplitudeAnalysis:
    def __init__(self, res1: list[float], res2: list[float]):
        super().__init__()
        self.result_q1 = res1
        self.result_q2 = res2
        self.frequency_tollerance = 2.5e6  # Hz
        self.amplitude_tollerance = 0.06

    def are_two_qubits_compatible(self):
        return self.are_frequencies_compatible() and self.are_amplitudes_compatible()

    def are_frequencies_compatible(self):
        return abs(self.result_q1[0] - self.result_q2[0]) < self.frequency_tollerance

    def are_amplitudes_compatible(self):
        return abs(self.result_q1[1] - self.result_q2[1]) < self.amplitude_tollerance

    def best_parameters(self):
        freq = (self.result_q1[0] + self.result_q2[0]) / 2
        amp = (self.result_q1[1] + self.result_q2[1]) / 2
        return [freq, amp]

class FrequencyVsAmplitudeAnalysis(BaseAnalysis):
    def __init__(self, dataset: xr.Dataset, freqs, amps):
        super().__init__()
        self.data_var = list(dataset.data_vars.keys())[0]
        self.S21 = dataset[self.data_var].values
        self.qubit = dataset[self.data_var].attrs["qubit"]
        dataset[f"y{self.qubit}"].values = np.abs(self.S21)
        self.dataset = dataset
        self.frequencies = freqs
        self.amplitudes = amps
        self.opt_freq = -1
        self.opt_amp = -1

    def plotter(self, axis: plt.Axes):
        datarray = self.dataset[f"y{self.qubit}"]

        if datarray.size == 0:
            raise ValueError(f"Data array for qubit {self.qubit} is empty.")

        # Plot the data array on the single plot
        datarray.plot(ax=axis, cmap="RdBu_r")
        # datarray.plot(ax=axis, x=f"cz_pulse_frequencies_sweep{self.qubit}", cmap="RdBu_r")
        # Scatter plot and lines on the same plot
        axis.scatter(
            self.opt_freq,
            self.opt_amp,
            c="r",
            label="CZ Amplitude = {:.3f} V".format(self.opt_amp),
            marker="X",
            s=200,
            edgecolors="k",
            linewidth=1.5,
            zorder=10,
        )
        axis.vlines(
            self.opt_freq,
            self.amplitudes[0],
            self.amplitudes[-1],
            label="Frequency Detuning = {:.2f} MHz".format(self.opt_freq / 1e6),
            colors="k",
            linestyles="--",
            linewidth=1.5,
        )
        axis.hlines(
            self.opt_amp,
            self.frequencies[0],
            self.frequencies[-1],
            colors="k",
            linestyles="--",
            linewidth=1.5,
        )

        axis.set_xlim([self.frequencies[0], self.frequencies[-1]])
        axis.set_ylim([self.amplitudes[0], self.amplitudes[-1]])
        axis.set_ylabel("Parametric Drive amplitude (V)")
        axis.set_xlabel("Frequency Detuning (Hz)")
        axis.set_title(f"CZ - Qubit {self.qubit[1:]}")
        axis.legend()  # Add legend to the plot

class FrequencyVsAmplitudeQ1Analysis(
    FrequencyVsAmplitudeAnalysis
):
    def __init__(self, dataset: xr.Dataset, freqs, amps):
        super().__init__(dataset, freqs, amps)

    def run_fitting(self) -> list[float, float]:
        print("WARNING TESTING CZ FREQUeNCY AND AMPLITUDE Q1 ANALYSIS")
        return self.run_fitting_find_max()

    def run_fitting_find_max(self):
        magnitudes = np.array(
            [[np.linalg.norm(u) for u in v] for v in self.dataset[f"y{self.qubit}"]]
        )
        magnitudes = np.transpose(
            (magnitudes - np.max(magnitudes))
            / (np.max(magnitudes) - np.max(magnitudes))
        )
        max_index = np.argmax(magnitudes)
        max_index = np.unravel_index(max_index, magnitudes.shape)
        self.opt_freq = self.frequencies[max_index[0]]
        self.opt_amp = self.amplitudes[max_index[1]]
        print(self.opt_freq, self.opt_amp)
        return [self.opt_freq, self.opt_amp]

class FrequencyVsAmplitudeQ2Analysis(
    FrequencyVsAmplitudeAnalysis
):
    def __init__(self, dataset: xr.Dataset, freqs, amps):
        super().__init__(dataset, freqs, amps)

    def run_fitting(self) -> list[float, float]:
        print("WARNING TESTING CZ FREQUeNCY AND AMPLITUDE Q2 ANALYSIS")
        return self.run_fitting_find_min()

    def run_fitting_find_min(self):
        magnitudes = np.array(
            [[np.linalg.norm(u) for u in v] for v in self.dataset[f"y{self.qubit}"]]
        )
        magnitudes = np.transpose(
            (magnitudes - np.min(magnitudes))
            / (np.max(magnitudes) - np.min(magnitudes))
        )
        min_index = np.argmin(magnitudes)
        min_index = np.unravel_index(min_index, magnitudes.shape)
        self.opt_freq = self.frequencies[min_index[0]]
        self.opt_amp = self.amplitudes[min_index[1]]
        print(self.opt_freq, self.opt_amp)
        return [self.opt_freq, self.opt_amp]
    
class CZParametrisationFixDurationAnalysis(BaseAnalysis):
    def __init__(self, dataset: xr.Dataset) -> None:
        super().__init__()
        self.dataset = dataset
        self.data_var = list(dataset.data_vars.keys())[0]
        self.opt_freq = -1
        self.opt_amp = -1
        self.opt_current = -1
        self.get_coordinates()
        self.process_dataset()
        pass

    def get_coordinates(self):
        for coord in self.dataset[self.data_var].coords:
            if "cz_parking_currents" in coord:
                self.number_of_currents = coord
            elif "cz_pulse_frequencies" in coord:
                self.frequency_coord = coord
            elif "cz_pulse_amplitude" in coord:
                self.amplitude_coord = coord

    def process_dataset(self):
        results = []
        self.fit_results = {}
        for current in self.number_of_currents:
            S21 = self.dataset[self.data_var].values
            d1 = np.abs(S21)
            q1 = FrequencyVsAmplitudeQ1Analysis(d1, self.frequency_coord, self.amplitude_coord )
            q1Res = q1.run_fitting()

            data_var = list(self.dataset.data_vars.keys())[1]
            S21 = self.dataset[data_var].values
            d2 = np.abs(S21)
            q2 = FrequencyVsAmplitudeQ2Analysis(d2, self.frequency_coord, self.amplitude_coord )
            q2Res = q2.run_fitting()
            c = CombinedFrequencyVsAmplitudeAnalysis(q1Res, q2Res)
            results.append(c, current) 

    def run_fitting(self) -> list[float, float]:
        print("WARNING TESTING CZ FREQUeNCY AND AMPLITUDE ANALYSIS")
        return self.run_analysis_on_freq_amp_results()

    def run_analysis_on_freq_amp_results(
        self,
        results: List[
            Tuple[CombinedFrequencyVsAmplitudeAnalysis, float]
        ],
    ):
        minCurrent = 1
        bestIndex = -1
        for index, result in enumerate(results):
            if result[0].are_two_qubits_compatible() and abs(result[1]) < minCurrent:
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

