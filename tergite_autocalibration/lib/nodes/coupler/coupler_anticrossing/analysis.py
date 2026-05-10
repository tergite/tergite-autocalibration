# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024, 2025
# (C) Copyright Michele Faucci Giannelli 2024, 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import ast
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import xarray

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.lib.base.analysis import (
    BaseAllCouplersAnalysis,
    BaseCouplerAnalysis,
)
from tergite_autocalibration.lib.nodes.qubit_control.spectroscopy.analysis import (
    QubitSpectroscopyMaxThresholdQubitAnalysis,
)
from tergite_autocalibration.lib.nodes.readout.resonator_spectroscopy.analysis import (
    ResonatorSpectroscopyQubitAnalysis,
)
from tergite_autocalibration.utils.dto.qoi import QOI
from tergite_autocalibration.utils.io.dataset import to_real_dataset


class CouplerAnticrossingAnalysis(BaseCouplerAnalysis):
    """
    This class analyzes the qubit spectroscopy data as a function of the current for a coupler.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def _find_crossing_currents(
        self,
        currents,
        frequencies,
        threshold=2e6,
        spurious_threshold=3e5,
        min_interval=0.0003,
        resonator_crossings=[],
        resonator_crossings_interval=0.00015,
    ):
        # Step 1: Clean up spurious values and fill in small gaps
        freqs = np.array(frequencies)
        currents = np.array(currents)
        nan_positions = np.isnan(freqs)
        freqs = freqs[~nan_positions]
        currents = currents[~nan_positions]

        for i in range(1, len(freqs) - 1):
            prev, curr, nxt = freqs[i - 1], freqs[i], freqs[i + 1]

            # Fill single zero gap if neighboring values are close
            if curr == 0 and abs(prev - nxt) < spurious_threshold:
                freqs[i] = (prev + nxt) / 2

            # Remove isolated non-zero point between zeros
            if prev == 0 and nxt == 0:
                freqs[i] = 0

        # Step 2: Find significant jumps across zero gaps
        temp_crossings = []
        crossing_currents = []

        i = 0
        while i < len(freqs) - 1:
            if freqs[i] == 0:
                i += 1
                continue

            # Look ahead to next non-zero point
            j = i + 1
            while j < len(freqs) and freqs[j] == 0:
                j += 1
            if j >= len(freqs):
                break

            if abs(freqs[i] - freqs[j]) > threshold:
                temp_crossings.append(currents[i])
                temp_crossings.extend(currents[i + 1 : j])
                temp_crossings.append(currents[j])

            # Evaluate grouping for minimum interval
            if (
                temp_crossings
                and (currents[i] - temp_crossings[0]) > min_interval
                or (len(temp_crossings) > 0 and j == len(freqs) - 1)
            ):
                mid_current = np.mean(temp_crossings)
                too_close = any(
                    abs(mid_current - rc) <= resonator_crossings_interval
                    for rc in resonator_crossings
                )

                if not too_close:
                    crossing_currents.append(mid_current)
                temp_crossings = []

            i += 1

        return crossing_currents

    def detect_peaks(self, qubit_specs_dataarray: xarray.DataArray):
        detected_frequencies = []
        detected_currents = []
        for current in self.dc_currents:
            ds = qubit_specs_dataarray.sel({self.current_coord: current})
            freq_analysis = QubitSpectroscopyMaxThresholdQubitAnalysis(ds)
            qubit_frequency = freq_analysis.process_qubit()
            detected_frequencies.append(qubit_frequency)
            detected_currents.append(current)
        return detected_frequencies, detected_currents

    def analyze_coupler(self):
        for coord in self.dataset[self.data_var].coords:
            if "frequencies" in coord:
                self.frequencies = coord
            elif "currents" in coord:
                self.current_coord = coord
                self.dc_currents = self.dataset[self.current_coord].values

        threshold = 2000000
        spurious_threshold = 300000
        min_interval = 0.0003
        resonator_crossings_interval = 0.00015

        control_qubit_magnitudes = xarray.ufuncs.abs(self.control_qubit_data_var)
        target_qubit_magnitudes = xarray.ufuncs.abs(self.target_qubit_data_var)
        (
            self.control_qubit_detected_frequencies,
            self.control_qubit_detected_currents,
        ) = self.detect_peaks(control_qubit_magnitudes)
        self.target_qubit_detected_frequencies, self.target_qubit_detected_currents = (
            self.detect_peaks(target_qubit_magnitudes)
        )
        self.resonator_crossing_points = []
        self.control_crossing_currents = self._find_crossing_currents(
            self.control_qubit_detected_currents,
            self.control_qubit_detected_frequencies,
            threshold,
            spurious_threshold,
            min_interval,
            self.resonator_crossing_points,
            resonator_crossings_interval,
        )
        self.target_crossing_currents = self._find_crossing_currents(
            self.target_qubit_detected_currents,
            self.target_qubit_detected_frequencies,
            threshold,
            spurious_threshold,
            min_interval,
            self.resonator_crossing_points,
            resonator_crossings_interval,
        )

        analysis_succesful = True
        analysis_result = {
            "control_qubit_crossing_points": {
                "value": self.control_crossing_currents,
                "error": 0,
            },
            "target_qubit_crossing_points": {
                "value": self.target_crossing_currents,
                "error": 0,
            },
        }

        qoi = QOI(analysis_result, analysis_succesful)
        return qoi

    def _get_resonator_crossing_points(self, coupler, qubit) -> List[float]:
        if REDIS_CONNECTION.hexists(
            f"couplers:{coupler}:{qubit}", "resonator_crossing_points"
        ):
            crossing_points_str = REDIS_CONNECTION.hget(
                f"couplers:{coupler}:{qubit}", "resonator_crossing_points"
            )
            try:
                # Convert the string representation to a Python list of floats
                crossing_points = list(
                    map(float, ast.literal_eval(crossing_points_str))
                )
            except (ValueError, SyntaxError) as e:
                raise ValueError(
                    f"Invalid format for crossing points: {crossing_points_str}"
                ) from e
        else:
            crossing_points = []

        return crossing_points

    def plotter(self, figures_dictionary: dict[str, list]):
        """
        Create the anticrossing figures and populate the figures dictionary.
        Args:
             figures_dictionary: A reference to the figures dictionary that the base
             analysis plots the key is the coupler labe and the value is a list
             containing the anticrossing figure for that coupler
        """
        figures_list = []
        fig, (ax1, ax2) = plt.subplots(2, 1)
        control_qubit_magnitudes = xarray.ufuncs.abs(self.control_qubit_data_var)
        target_qubit_magnitudes = xarray.ufuncs.abs(self.target_qubit_data_var)
        control_qubit_magnitudes.plot(ax=ax1, x=self.current_coord)
        target_qubit_magnitudes.plot(ax=ax2, x=self.current_coord)

        ax1.scatter(
            self.control_qubit_detected_currents,
            self.control_qubit_detected_frequencies,
            s=52,
            c="red",
        )
        for cross_current in self.control_crossing_currents:
            ax1.axvline(
                cross_current,
                color="grey",
                linestyle="dashed",
                linewidth=2,
            )
        ax2.scatter(
            self.target_qubit_detected_currents,
            self.target_qubit_detected_frequencies,
            s=52,
            c="red",
        )
        for cross_current in self.target_crossing_currents:
            ax2.axvline(
                cross_current,
                color="grey",
                linestyle="dashed",
                linewidth=2,
            )
        figures_list.append(fig)
        figures_dictionary[self.coupler] = figures_list
        return


class ResonatorSpectroscopyVsCurrentCouplerAnalysis(BaseCouplerAnalysis):
    """
    This class analyzes the resonator spectroscopy data as a function of the current for a coupler.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def detect_peaks(self, res_specs_dataarray: xarray.DataArray):
        detected_frequencies = []
        detected_currents = []
        for current in self.dc_currents:
            darray = res_specs_dataarray.sel({self.current_coord: current})
            real_ds = to_real_dataset(darray.to_dataset())
            real_ds = real_ds.drop_vars(self.current_coord)
            freq_analysis = ResonatorSpectroscopyQubitAnalysis(self.name, "")
            resonator_frequency = freq_analysis.process_qubit(
                real_ds, self.data_var[1:]
            ).analysis_result["clock_freqs:readout"]["value"]
            detected_frequencies.append(resonator_frequency)
            detected_currents.append(current)
        return detected_frequencies, detected_currents

    def _find_crossing_currents(
        self,
        currents,
        frequencies,
        threshold=2e6,
        spurious_threshold=3e5,
        min_interval=0.0003,
        resonator_crossings=[],
        resonator_crossings_interval=0.00015,
    ):
        # Step 1: Clean up spurious values and fill in small gaps
        freqs = frequencies.copy()

        for i in range(1, len(freqs) - 1):
            prev, curr, nxt = freqs[i - 1], freqs[i], freqs[i + 1]

            # Fill single zero gap if neighboring values are close
            if curr == 0 and abs(prev - nxt) < spurious_threshold:
                freqs[i] = (prev + nxt) / 2

            # Remove isolated non-zero point between zeros
            if prev == 0 and nxt == 0:
                freqs[i] = 0

        # Step 2: Find significant jumps across zero gaps
        temp_crossings = []
        crossing_currents = []

        i = 0
        while i < len(freqs) - 1:
            # Look ahead to next non-zero point
            j = i + 1
            while j < len(freqs) and freqs[j] == 0:
                j += 1
            if j >= len(freqs):
                break

            if freqs[i] == 0:
                i += 1
                continue

            # Detect transition
            if abs(freqs[i] - freqs[j]) > threshold:
                temp_crossings.append(currents[i])
                temp_crossings.extend(currents[i + 1 : j])
                temp_crossings.append(currents[j])

            # Evaluate grouping for minimum interval
            if temp_crossings:
                span = currents[j] - min(temp_crossings)
                if span > min_interval or j == len(freqs) - 1:
                    mid_current = np.mean(temp_crossings)
                    too_close = any(
                        abs(mid_current - rc) <= resonator_crossings_interval
                        for rc in resonator_crossings
                    )

                    if not too_close:
                        crossing_currents.append(mid_current)
                    temp_crossings = []

            i += 1

        return crossing_currents

    def analyze_coupler(self):
        """
        This function analyzes the coupler data to find crossing currents for both qubits.
        """
        for coord in self.dataset[self.data_var].coords:
            if "frequencies" in coord:
                self.frequencies = coord
            elif "currents" in coord:
                self.current_coord = coord
                self.dc_currents = self.dataset[self.current_coord].values

        threshold = 30000
        spurious_threshold = 4000
        min_interval = 0.0005  # Adjust based on data range

        # control_qubit_magnitudes = xarray.ufuncs.abs(self.control_qubit_data_var)
        # target_qubit_magnitudes = xarray.ufuncs.abs(self.target_qubit_data_var)
        self.control_qubit_detected_frequencies, self.target_qubit_detected_currents = (
            self.detect_peaks(self.control_qubit_data_var)
        )
        self.target_qubit_detected_frequencies, self.control_qubit_detected_currents = (
            self.detect_peaks(self.target_qubit_data_var)
        )
        self.control_crossing_currents = self._find_crossing_currents(
            self.control_qubit_detected_currents,
            self.control_qubit_detected_frequencies,
            threshold,
            spurious_threshold,
            min_interval,
        )
        self.target_crossing_currents = self._find_crossing_currents(
            self.target_qubit_detected_currents,
            self.target_qubit_detected_frequencies,
            threshold,
            spurious_threshold,
            min_interval,
        )

        analysis_succesful = True
        analysis_result = {
            "control_resonator_crossing_points": {
                "value": self.control_crossing_currents,
                "error": 0,
            },
            "target_resonator_crossing_points": {
                "value": self.target_crossing_currents,
                "error": 0,
            },
        }
        qoi = QOI(analysis_result, analysis_succesful)
        return qoi

    def plotter(self, figures_dictionary):
        """
        Create the anticrossing figures and populate the figures dictionary.
        Args:
             figures_dictionary: A reference to the figures dictionary that the base
             analysis plots the key is the coupler labe and the value is a list
             containing the anticrossing figure for that coupler
        """
        figures_list = []
        fig, (ax1, ax2) = plt.subplots(1, 2)
        control_qubit_magnitudes = xarray.ufuncs.abs(self.control_qubit_data_var)
        target_qubit_magnitudes = xarray.ufuncs.abs(self.target_qubit_data_var)
        control_qubit_magnitudes.plot(ax=ax1)
        target_qubit_magnitudes.plot(ax=ax2)
        ax1.scatter(
            self.control_qubit_detected_frequencies,
            self.control_qubit_detected_currents,
            s=52,
            c="red",
        )
        for cross_current in self.control_crossing_currents:
            ax1.axhline(
                cross_current,
                color="grey",
                linestyle="dashed",
                linewidth=2,
            )
        ax2.scatter(
            self.target_qubit_detected_frequencies,
            self.target_qubit_detected_currents,
            s=52,
            c="red",
        )
        for cross_current in self.target_crossing_currents:
            ax2.axhline(
                cross_current,
                color="grey",
                linestyle="dashed",
                linewidth=2,
            )
        figures_list.append(fig)
        figures_dictionary[self.coupler] = figures_list
        return


class ResonatorSpectroscopyVsCurrentNodeAnalysis(BaseAllCouplersAnalysis):
    """
    This class analyzes the resonator spectroscopy data as a function of the current for all coupler.
    """

    single_coupler_analysis_obj = ResonatorSpectroscopyVsCurrentCouplerAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)


class CouplerAnticrossingNodeAnalysis(BaseAllCouplersAnalysis):
    """
    This class analyzes the qubit spectroscopy data as a function of the current for all coupler.
    """

    single_coupler_analysis_obj = CouplerAnticrossingAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
