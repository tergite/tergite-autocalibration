# This code is part of Tergite
#
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import warnings
from typing import List, Tuple

import numpy as np
import xarray as xr
from matplotlib import pyplot as plt

from .utils.no_valid_combination_exception import (
    NoValidCombinationException,
)
from ....base.analysis import BaseAnalysis, BaseCouplerAnalysis


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
        self.qubit = -1
        self.dataset = dataset
        self.frequencies = freqs
        self.amplitudes = amps
        self.opt_freq = -1
        self.opt_amp = -1

    def plotter(self, axis: plt.Axes):
        datarray = self.dataset[f"y{self.qubit}"]
        if not isinstance(datarray, xr.DataArray):
            raise TypeError("Expected datarray to be an xarray.DataArray")
        datarray = datarray.fillna(0)
        print(datarray)

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


class FrequencyVsAmplitudeQ1Analysis(FrequencyVsAmplitudeAnalysis):
    def __init__(self, dataset: xr.Dataset, freqs, amps):
        super().__init__(dataset, freqs, amps)
        # print(dataset)
        self.data_var = list(dataset.data_vars.keys())[0]
        self.qubit = dataset[self.data_var].attrs["qubit"]
        # ds_real = dataset[self.data_var].isel(ReIm=0)
        # ds_imag = dataset[self.data_var].isel(ReIm=1)
        # ds = ds_real + 1j * ds_imag
        # S21 = ds.values
        S21 = dataset[self.data_var].values
        abs_S21 = np.abs(S21)
        print("coordinates")
        print(dataset.coords)
        dataset[f"y{self.qubit}"] = xr.DataArray(
            abs_S21, dims=dataset.dims, coords=dataset.coords
        )  # Ensure dims and coords match
        self.dataset = dataset

    def analyse_qubit(self) -> list[float, float]:
        print("Running FrequencyVsAmplitudeQ1Analysis")
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


class FrequencyVsAmplitudeQ2Analysis(FrequencyVsAmplitudeAnalysis):
    def __init__(self, dataset: xr.Dataset, freqs, amps):
        super().__init__(dataset, freqs, amps)
        # print(dataset)
        self.data_var = list(dataset.data_vars.keys())[1]
        self.qubit = dataset[self.data_var].attrs["qubit"]
        # ds_real = dataset[self.data_var].isel(ReIm=0)
        # ds_imag = dataset[self.data_var].isel(ReIm=1)
        # ds = ds_real + 1j * ds_imag
        S21 = dataset[self.data_var].values
        abs_S21 = np.abs(S21)
        dataset[f"y{self.qubit}"] = xr.DataArray(
            abs_S21, dims=dataset.dims, coords=dataset.coords
        )  # Ensure dims and coords match
        self.dataset = dataset

    def analyse_qubit(self) -> list[float, float]:
        print("Running FrequencyVsAmplitudeQ2Analysis")
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


class CZParametrisationFixDurationAnalysis(BaseCouplerAnalysis):
    def __init__(self) -> None:
        super().__init__()
        print(self.dataset)
        print(list(self.dataset.data_vars.keys()))
        self.data_var = list(self.dataset.data_vars.keys())[0]
        self.data_path = ""
        self.opt_freq = -1
        self.opt_amp = -1
        self.opt_current = -1
        self.q1_list = []
        self.q2_list = []
        self.get_coordinates()
        pass

    def get_coordinates(self):
        for coord in self.dataset[self.data_var].coords:
            if "cz_parking_currents" in coord:
                self.current_coord = coord
                self.current_values = self.dataset[coord].values
            elif "cz_pulse_frequencies" in coord:
                self.frequency_coord = coord
                self.frequency_values = self.dataset[coord].values
            elif "cz_pulse_amplitude" in coord:
                self.amplitude_coord = coord
                self.amplitude_values = self.dataset[coord].values

    def analyse_qubit(self) -> list[float, float, float]:
        print("Running CZParametrisationFixDurationAnalysis")
        results = self.process_dataset()
        return self.run_analysis_on_freq_amp_results(results)

    def process_dataset(
        self,
    ) -> List[Tuple[CombinedFrequencyVsAmplitudeAnalysis, float]]:
        results = []
        self.fit_results = {}
        for current_index, current in enumerate(self.current_values):
            print(f"Processing current index: {current_index}, value: {current}")
            sliced_dataset = self.dataset.isel({self.current_coord: current_index})
            print(sliced_dataset.dims)
            print(sliced_dataset.coords)
            sliced_dataset = sliced_dataset.drop_vars(self.current_coord)
            print("Dimensions after slicing:", sliced_dataset.dims)
            print("Coordinates after slicing:", sliced_dataset.coords)

            # Plot the dataset
            import matplotlib.pyplot as plt

            sliced_dataset.plot()
            plt.show()

            q1 = FrequencyVsAmplitudeQ1Analysis(
                sliced_dataset, self.frequency_values, self.amplitude_values
            )
            q1Res = q1.analyse_qubit()

            q2 = FrequencyVsAmplitudeQ2Analysis(
                sliced_dataset, self.frequency_values, self.amplitude_values
            )
            q2Res = q2.analyse_qubit()
            c = CombinedFrequencyVsAmplitudeAnalysis(q1Res, q2Res)
            results.append([c, current])

        self.q1_list.append(q1)
        self.q2_list.append(q2)

        return results

    def run_analysis_on_freq_amp_results(
        self, results: List[Tuple[CombinedFrequencyVsAmplitudeAnalysis, float]]
    ):
        minCurrent = 1
        bestIndex = -1
        for index, result in enumerate(results):
            print(result)
            if result[0].are_two_qubits_compatible() and abs(result[1]) < minCurrent:
                minCurrent = result[1]
                bestIndex = index

        if bestIndex == -1:
            raise NoValidCombinationException

        self.opt_index = bestIndex
        self.opt_freq = results[bestIndex][0].best_parameters()[0]
        self.opt_amp = results[bestIndex][0].best_parameters()[1]
        self.opt_current = minCurrent

        print("Best values are:")
        print("  - freq: " + str(self.opt_freq))
        print("  - amp: " + str(self.opt_amp))
        print("  - current: " + str(self.opt_current))
        return [self.opt_freq, self.opt_amp, self.opt_current]

    def plotter(seld, axis):
        pass

    def plotter_v2(self, data_path):
        for index, e in enumerate(self.q1_list):
            fig, axs = plt.subplots(
                nrows=1,
                ncols=2,
                squeeze=False,
                figsize=(2, 1),
            )
            self.q1_list[index].plotter(axs[0])
            self.q2_list[index].plotter(axs[1])

            fig = plt.gcf()
            fig.set_tight_layout(True)
            name = "CZParametrisationFixDurationAnalysis_" + str(
                self.current_values[index]
            )
            try:
                fig.savefig(f"{data_path}/{name}.png", bbox_inches="tight", dpi=400)
            except FileNotFoundError:
                warnings.warn("File Not existing")
                pass
