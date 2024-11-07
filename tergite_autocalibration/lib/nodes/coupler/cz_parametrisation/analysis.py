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

import matplotlib.patches as mpatches
import numpy as np
import xarray as xr
from matplotlib import pyplot as plt

from tergite_autocalibration.lib.base.analysis import (
    BaseAllCouplersRepeatAnalysis,
    BaseCouplerAnalysis,
    BaseQubitAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.utils.no_valid_combination_exception import (
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


class FrequencyVsAmplitudeQubitAnalysis(BaseQubitAnalysis):
    def __init__(self, name, redis_fields, freqs, amps):
        super().__init__(name, redis_fields)
        self.qubit = -1
        self.frequencies = freqs
        self.amplitudes = amps
        self.opt_freq = -1
        self.opt_amp = -1

    def process_qubit(self, dataset, qubit_var_name):
        # Access the specific DataArray for the qubit
        if qubit_var_name not in dataset.data_vars:
            raise ValueError(
                f"Qubit data variable {qubit_var_name} not found in dataset."
            )

        # Now, self.data_var points to the relevant DataArray for this qubit
        self.data_var = dataset[qubit_var_name]
        self.dataset = dataset
        self.qubit = qubit_var_name[1:]  # dataset.attrs["qubit"]
        self.coord = dataset.coords
        self.S21 = dataset.isel(ReIm=0) + 1j * dataset.isel(ReIm=1)
        self.magnitudes = np.abs(self.S21)
        self._qoi = self.analyse_qubit()

        return self._qoi

    def plotter(self, axis: plt.Axes):
        datarray = self.magnitudes[f"y{self.qubit}"]

        if not isinstance(datarray, xr.DataArray):
            raise TypeError("Expected datarray to be an xarray.DataArray")
        datarray = datarray.fillna(0)

        if datarray.size == 0:
            raise ValueError(f"Data array for qubit {self.qubit} is empty.")

        # Plot the data array on the single plot
        for coord in datarray.coords:
            if "cz_parking_currents" in coord:
                datarray = datarray.drop(coord)

        for dim in datarray.dims:
            if "cz_parking_currents" in dim:
                # If it's not needed, you can drop it
                datarray = datarray.squeeze(dim, drop=True)

        datarray.plot(ax=axis, cmap="RdBu_r")

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

        # Customize plot as needed
        handles, labels = axis.get_legend_handles_labels()
        patch = mpatches.Patch(color="red", label=f"{self.qubit}")
        handles.append(patch)
        axis.legend(handles=handles, fontsize="small")


class FrequencyVsAmplitudeQ1Analysis(FrequencyVsAmplitudeQubitAnalysis):
    def __init__(self, name, redis_fields, freqs, amps):
        super().__init__(name, redis_fields, freqs, amps)

    def analyse_qubit(self) -> list[float, float]:
        print("Running FrequencyVsAmplitudeQ1Analysis")
        return self.run_fitting_find_max()

    def run_fitting_find_max(self):
        magnitudes = np.array(
            [[np.linalg.norm(u) for u in v] for v in self.magnitudes[f"y{self.qubit}"]]
        )
        magnitudes = np.transpose(
            (magnitudes - np.max(magnitudes))
            / (np.max(magnitudes) - np.max(magnitudes))
        )
        max_index = np.argmax(magnitudes)
        max_index = np.unravel_index(max_index, magnitudes.shape)
        self.opt_freq = self.frequencies[max_index[0]]
        self.opt_amp = self.amplitudes[max_index[1]]
        # print(self.opt_freq, self.opt_amp)
        return [self.opt_freq, self.opt_amp]


class FrequencyVsAmplitudeQ2Analysis(FrequencyVsAmplitudeQubitAnalysis):
    def __init__(self, name, redis_fields, freqs, amps):
        super().__init__(name, redis_fields, freqs, amps)

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
        # print(self.opt_freq, self.opt_amp)
        return [self.opt_freq, self.opt_amp]


class CZParametrisationFixDurationCouplerAnalysis(BaseCouplerAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.data_path = ""
        self.opt_freq = -1
        self.opt_amp = -1
        self.opt_current = -1
        self.q1_list = []
        self.q2_list = []
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

    def analyze_coupler(self) -> list[float, float, float]:
        print("Running CZParametrisationFixDurationAnalysis")
        results = self.run_coupler()
        return self.run_analysis_on_freq_amp_results(results)

    def run_coupler(
        self,
    ) -> List[Tuple[CombinedFrequencyVsAmplitudeAnalysis, float]]:
        results = []
        self.fit_results = {}
        self.get_coordinates()

        for current_index, current in enumerate(self.current_values):
            print(f"Processing current index: {current_index}, value: {current}")

            q1_data_var = [
                data_var
                for data_var in self.dataset.data_vars
                if self.name_qubit_1 in data_var
            ]
            ds1 = self.dataset[q1_data_var]
            matching_coords = [
                coord for coord in ds1.coords if self.name_qubit_1 in coord
            ]
            if matching_coords:
                selected_coord_name = matching_coords[0]
                ds1 = ds1.sel({selected_coord_name: slice(None)})
                ds1 = ds1.sel({self.current_coord: current})
            # print(type(sliced_dataset))
            # print(sliced_dataset.dims)
            # print(sliced_dataset.coords)
            # sliced_dataset = sliced_dataset.drop_vars(self.current_coord)
            # print("Dimensions after slicing:", sliced_dataset.dims)
            # print("Coordinates after slicing:", sliced_dataset.coords)

            q1 = FrequencyVsAmplitudeQ1Analysis(
                self.name,
                self.redis_fields,
                self.frequency_values,
                self.amplitude_values,
            )
            q1Res = q1.process_qubit(ds1, q1_data_var[0])

            q2_data_var = [
                data_var
                for data_var in self.dataset.data_vars
                if self.name_qubit_2 in data_var
            ]
            ds2 = self.dataset[q2_data_var]
            matching_coords = [
                coord for coord in ds2.coords if self.name_qubit_2 in coord
            ]
            if matching_coords:
                selected_coord_name = matching_coords[0]
                ds2 = ds2.sel({selected_coord_name: slice(None)})
                ds2 = ds2.sel({self.current_coord: current})

            q2 = FrequencyVsAmplitudeQ2Analysis(
                self.name,
                self.redis_fields,
                self.frequency_values,
                self.amplitude_values,
            )
            q2Res = q2.process_qubit(ds2, q2_data_var[0])

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
            # print(result)
            if result[0].are_two_qubits_compatible() and abs(result[1]) < minCurrent:
                minCurrent = result[1]
                bestIndex = index

        if bestIndex == -1:
            print(
                "Bad data, no combination found, plotting all results to visual inspection. Exiting."
            )
            self.plot_all()
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

    def plotter(self, primary_axis, secondary_axis):
        self.q1_list[self.opt_index].plotter(primary_axis)
        self.q2_list[self.opt_index].plotter(secondary_axis)

    def plot_all(self):
        for index, e in enumerate(self.q1_list):
            fig, axs = plt.subplots(
                nrows=1,
                ncols=2,
                squeeze=False,
                figsize=(10, 5),
            )

            self.q1_list[index].plotter(axs[0, 0])
            self.q2_list[index].plotter(axs[0, 1])

            fig = plt.gcf()
            fig.set_tight_layout(True)
            name = "CZParametrisationFixDurationAnalysis_" + str(
                self.current_values[index]
            )
            try:
                fig.savefig(
                    f"{self.data_path}/{name}.png", bbox_inches="tight", dpi=400
                )
            except FileNotFoundError:
                warnings.warn("File Not existing")
                pass


class CZParametrisationFixDurationNodeAnalysis(BaseAllCouplersRepeatAnalysis):
    single_coupler_analysis_obj = CZParametrisationFixDurationCouplerAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.repeat_coordinate_name = "cz_parking_currents"

    def save_plots(self):
        super().save_plots()
        for analysis in self.coupler_analyses:
            analysis.plot_all()
