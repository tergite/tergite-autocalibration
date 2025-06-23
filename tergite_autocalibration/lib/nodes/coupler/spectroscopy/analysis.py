# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
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
from pathlib import Path
from typing import List
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.lib.base.analysis import (
    BaseAllCouplersAnalysis,
    BaseCouplerAnalysis,
    BaseQubitAnalysis,
)
from tergite_autocalibration.lib.base.utils.figure_utils import (
    create_figure_with_top_band,
)
from tergite_autocalibration.lib.nodes.qubit_control.spectroscopy.analysis import (
    QubitSpectroscopyMaxThresholdQubitAnalysis,
)
from tergite_autocalibration.lib.nodes.readout.resonator_spectroscopy.analysis import (
    ResonatorSpectroscopyQubitAnalysis,
)
from tergite_autocalibration.utils.logging import logger
from tergite_autocalibration.utils.dto.qoi import QOI


class QubitSpectroscopyVsCurrentQubitAnalysis(BaseQubitAnalysis):
    """
    This class analyzes the qubit frequencies as obtained from the scpescroscopies to find crossing currents.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.resonator_crossing_points = []
        self.crossing_currents = []
        self.n_crossing = 0
        self.detected_frequencies = []
        self.detected_currents = []
        self.spectroscopy_analyses = []
        self.frequencies_coord = None
        self.current_coord = None
        self.frequencies = None
        self.dc_currents = None

    def analyse_qubit(self) -> list[float, float]:
        """
        This function analyzes the qubit spectroscopy data to find crossing currents.
        It processes the dataset, identifies the frequencies and currents, and
        applies a threshold to find the crossing points.

        Returns:
            list: A list of crossing currents.
        """

        logger.debug("Running QubitAnalysisForCouplerSpectroscopy")

        for coord in self.dataset[self.data_var].coords:
            if "frequencies" in coord:
                self.frequencies_coord = coord
            elif "currents" in coord:
                self.current_coord = coord

        self.dc_currents = self.dataset[self.current_coord]
        self.frequencies = self.dataset[self.frequencies_coord]

        for i, current in enumerate(self.dc_currents.values):
            ds = self.dataset.sel({self.current_coord: current})
            # Optionally drop the 'dc_currentsq09_q10' if it's not needed
            for coord in self.magnitudes.coords:
                if "dc_currents" in coord:
                    ds = ds.drop_vars(coord)
            freq_analysis = QubitSpectroscopyMaxThresholdQubitAnalysis(
                self.name, "", current
            )
            qubit_frequency = freq_analysis.process_qubit(
                ds, self.data_var[1:]
            ).analysis_result["clock_freqs:f01"]["value"]
            self.spectroscopy_analyses.append(freq_analysis)

            if not np.isnan(qubit_frequency):
                self.detected_frequencies.append(qubit_frequency)
                self.detected_currents.append(current)
            else:
                self.detected_frequencies.append(0)
                self.detected_currents.append(current)

        threshold = 2000000
        spurious_threshold = 300000
        min_interval = 0.0003
        resonator_crossings_interval = 0.00015

        self.crossing_currents = self._find_crossing_currents(
            self.detected_currents,
            self.detected_frequencies,
            threshold,
            spurious_threshold,
            min_interval,
            self.resonator_crossing_points,
            resonator_crossings_interval,
        )

        self.n_crossing = len(self.crossing_currents)
        return [str(self.crossing_currents)]

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
            if freqs[i] == 0:
                i += 1
                continue

            # Look ahead to next non-zero point
            j = i + 1
            while j < len(freqs) and freqs[j] == 0:
                j += 1
            if j >= len(freqs):
                break

            # Detect transition
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

    def plotter(self, ax: plt.Axes):
        """
        Plot the detected frequencies and currents, along with crossing currents.
        Args:
            ax (plt.Axes): The axes to plot on.
        """

        self.magnitudes[self.data_var].plot(ax=ax, x=self.current_coord)
        ax.scatter(self.detected_currents, self.detected_frequencies, s=52, c="blue")
        ax.vlines(
            self.crossing_currents[0],
            min(self.frequencies),
            max(self.frequencies),
            color="grey",
            linestyles="dashed",
            linewidth=2,
            alpha=0.8,
        )
        if self.n_crossing > 1:
            ax.vlines(
                self.crossing_currents[1],
                min(self.frequencies),
                max(self.frequencies),
                color="grey",
                linestyles="dashed",
            )
        if self.n_crossing > 2:
            ax.vlines(
                self.crossing_currents[2],
                min(self.frequencies),
                max(self.frequencies),
                color="grey",
                linestyles="dashed",
            )
        if self.n_crossing > 3:
            ax.vlines(
                self.crossing_currents[3],
                min(self.frequencies),
                max(self.frequencies),
                color="grey",
                linestyles="dashed",
            )
        # ax.ylim([min(self.peak), max(self.peak)])
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.set_xlabel("Coupler current [A]")
        ax.set_ylabel("Frequency [Hz]")
        ax.set_title(f"Qubit {self.qubit}")


class ResonatorSpectroscopyVsCurrentQubitAnalysis(BaseQubitAnalysis):
    """
    This class analyzes the resonator spectroscopy fitted frequencies to find crossing currents.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.detected_frequencies = []
        self.detected_currents = []
        self.spectroscopy_analyses = []
        self.crossing_currents = []
        self.n_crossing = 0
        self.frequencies_coord = None
        self.current_coord = None
        self.frequencies = None
        self.dc_currents = None

    def analyse_qubit(self) -> list[float, float]:
        """
        This function analyzes the resonator spectroscopy data to find crossing currents.
        It processes the dataset, identifies the frequencies and currents, and
        applies a threshold to find the crossing points.

        Returns:
            list: A list of crossing currents.
        """

        logger.debug("Running QubitAnalysisForCouplerSpectroscopy")

        for coord in self.dataset[self.data_var].coords:
            if "frequencies" in coord:
                self.frequencies_coord = coord
            elif "currents" in coord:
                self.current_coord = coord

        self.dc_currents = self.dataset[self.current_coord]
        self.frequencies = self.dataset[self.frequencies_coord]

        for i, current in enumerate(self.dc_currents.values):
            ds = self.dataset.sel({self.current_coord: current})

            for coord in self.magnitudes.coords:
                if "dc_currents" in coord:
                    ds = ds.drop_vars(coord)

            freq_analysis = ResonatorSpectroscopyQubitAnalysis(self.name, "")
            resonator_frequency = freq_analysis.process_qubit(
                ds, self.data_var[1:]
            ).analysis_result["clock_freqs:readout"]["value"]

            self.spectroscopy_analyses.append(freq_analysis)

            if not np.isnan(resonator_frequency):
                self.detected_frequencies.append(resonator_frequency)
                self.detected_currents.append(current)
            else:
                self.detected_frequencies.append(0)
                self.detected_currents.append(current)

        threshold = 30000
        spurious_threshold = 4000
        min_interval = 0.0005  # Adjust based on data range

        self.crossing_currents = self._find_crossing_currents(
            self.detected_currents,
            self.detected_frequencies,
            threshold,
            spurious_threshold,
            min_interval,
        )
        self.n_crossing = len(self.crossing_currents)

        if self.n_crossing == 0:
            max_freq_index = np.argmax(self.detected_frequencies)
            self.crossing_currents.append(self.detected_currents[max_freq_index])
            logger.info(
                f"No crossings detected. Using current with highest frequency: {self.detected_currents[max_freq_index]} ({self.detected_frequencies[max_freq_index]})"
            )
            self.n_crossing = 1

        return [str(self.crossing_currents)]

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

    def plotter(self, ax: plt.Axes):
        """
        Plot the detected frequencies and currents, along with crossing currents.
        Args:
            ax (plt.Axes): The axes to plot on.
        """
        ax.scatter(self.detected_currents, self.detected_frequencies, s=52, c="blue")
        if self.n_crossing > 0:
            ax.vlines(
                self.crossing_currents[0],
                min(self.frequencies),
                max(self.frequencies),
                color="grey",
                linestyles="dashed",
                linewidth=2,
                alpha=0.8,
            )
        if self.n_crossing > 1:
            ax.vlines(
                self.crossing_currents[1],
                min(self.frequencies),
                max(self.frequencies),
                color="grey",
                linestyles="dashed",
            )
        if self.n_crossing > 2:
            ax.vlines(
                self.crossing_currents[2],
                min(self.frequencies),
                max(self.frequencies),
                color="grey",
                linestyles="dashed",
            )
        if self.n_crossing > 3:
            ax.vlines(
                self.crossing_currents[3],
                min(self.frequencies),
                max(self.frequencies),
                color="grey",
                linestyles="dashed",
            )
        ax.set_ylim([min(self.detected_frequencies), max(self.detected_frequencies)])
        ax.set_xlabel("Coupler current [A]")
        ax.set_ylabel("Frequency [Hz]")
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5))


class QubitSpectroscopyVsCurrentCouplerAnalysis(BaseCouplerAnalysis):
    """
    This class analyzes the qubit spectroscopy data as a function of the current for a coupler.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.q1_analysis = None
        self.q2_analysis = None
        self.frequencies = None
        self.current_coord = None
        self.frequencies_coord = None

    def analyze_coupler(self):
        for coord in self.dataset[self.data_var].coords:
            if "frequencies" in coord:
                self.frequencies = coord
            elif "currents" in coord:
                self.currents = coord
                self.current_coord = coord

        self.q1_analysis = QubitSpectroscopyVsCurrentQubitAnalysis(
            self.name, self.redis_fields
        )
        self.q2_analysis = QubitSpectroscopyVsCurrentQubitAnalysis(
            self.name, self.redis_fields
        )

        resonator_crossing_points_q1 = self.get_resonator_crossing_points(
            self.coupler, self.name_qubit_1
        )

        self.q1_analysis.resonator_crossing_points = resonator_crossing_points_q1

        q1_data_var = [
            data_var
            for data_var in self.dataset.data_vars
            if self.name_qubit_1 in data_var
        ]
        ds1 = self.dataset[q1_data_var]

        q1result = self.q1_analysis.process_qubit(ds1, self.name_qubit_1)

        resonator_crossing_points_q2 = self.get_resonator_crossing_points(
            self.coupler, self.name_qubit_2
        )
        self.q2_analysis.resonator_crossing_points = resonator_crossing_points_q2

        q2_data_var = [
            data_var
            for data_var in self.dataset.data_vars
            if self.name_qubit_2 in data_var
        ]
        ds2 = self.dataset[q2_data_var]
        q2result = self.q2_analysis.process_qubit(ds2, self.name_qubit_2)
        analysis_succesful = True
        analysis_result = {
            self.name_qubit_1: (dict(zip(self.redis_fields, q1result))),
            self.name_qubit_2: (dict(zip(self.redis_fields, q2result))),
        }

        qoi = QOI(analysis_result, analysis_succesful)
        return qoi

    def get_resonator_crossing_points(self, coupler, qubit) -> List[float]:
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
            except (ValueError, SyntaxError):
                raise ValueError(
                    f"Invalid format for crossing points: {crossing_points_str}"
                )
        else:
            crossing_points = []

        return crossing_points

    def plotter(self, primary_axis, secondary_axis):
        """
        Plot the results of the analysis on the provided axes.
        Args:
            primary_axis (plt.Axes): The primary axis for the first qubit.
            secondary_axis (plt.Axes): The secondary axis for the second qubit.
        """

        self.q1_analysis.plotter(primary_axis)
        self.q2_analysis.plotter(secondary_axis)

    def _plot_all_fit_q1(self, axs, columns):
        for i, ana in enumerate(self.q1_analysis.spectroscopy_analyses):
            ana.plotter(axs[int(i / columns), i % columns])

    def _plot_all_fit_q2(self, axs, columns):
        for i, ana in enumerate(self.q2_analysis.spectroscopy_analyses):
            ana.plotter(axs[int(i / columns), i % columns])

    def plot_spectroscopies(self, data_path: Path):
        """
        Plot all the spectroscopy analyses for both qubits and save the figures.
        """
        n_analyses = len(self.q1_analysis.spectroscopy_analyses)
        columns = int(np.ceil(np.sqrt(n_analyses)))
        rows = int(np.ceil(n_analyses / columns))
        fig, axs = create_figure_with_top_band(rows, columns)
        self._plot_all_fit_q1(axs, columns)

        full_path = (
            data_path
            / f"{self.name}_{self.coupler}_{self.name_qubit_1}_spectroscopies.png"
        )
        fig.savefig(full_path, bbox_inches="tight", dpi=200)

        fig, axs = create_figure_with_top_band(rows, columns)
        self._plot_all_fit_q2(axs, columns)

        full_path = (
            data_path
            / f"{self.name}_{self.coupler}_{self.name_qubit_2}_spectroscopies.png"
        )
        fig.savefig(full_path, bbox_inches="tight", dpi=200)
        plt.close()


class ResonatorSpectroscopyVsCurrentCouplerAnalysis(BaseCouplerAnalysis):
    """
    This class analyzes the resonator spectroscopy data as a function of the current for a coupler.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.q1_analysis = None
        self.q2_analysis = None
        self.frequencies = None
        self.current_coord = None
        self.frequencies_coord = None

    def analyze_coupler(self):
        """
        This function analyzes the coupler data to find crossing currents for both qubits.
        """
        for coord in self.dataset[self.data_var].coords:
            if "frequencies" in coord:
                self.frequencies = coord
            elif "currents" in coord:
                self.currents = coord
                self.current_coord = coord

        self.q1_analysis = ResonatorSpectroscopyVsCurrentQubitAnalysis(
            self.name, self.redis_fields
        )
        self.q2_analysis = ResonatorSpectroscopyVsCurrentQubitAnalysis(
            self.name, self.redis_fields
        )

        q1_data_var = [
            data_var
            for data_var in self.dataset.data_vars
            if self.name_qubit_1 in data_var
        ]
        ds1 = self.dataset[q1_data_var]
        q1result = self.q1_analysis.process_qubit(ds1, q1_data_var[0][1:])
        q2_data_var = [
            data_var
            for data_var in self.dataset.data_vars
            if self.name_qubit_2 in data_var
        ]
        ds2 = self.dataset[q2_data_var]
        q2result = self.q2_analysis.process_qubit(ds2, q2_data_var[0][1:])

        analysis_succesful = True
        analysis_result = {
            self.name_qubit_1: (dict(zip(self.redis_fields, q1result))),
            self.name_qubit_2: (dict(zip(self.redis_fields, q2result))),
        }

        qoi = QOI(analysis_result, analysis_succesful)
        return qoi

    def plotter(self, primary_axis, secondary_axis):
        self.q1_analysis.plotter(primary_axis)
        self.q2_analysis.plotter(secondary_axis)

    def _plot_all_fit_q1(self, axs, columns):
        for i, ana in enumerate(self.q1_analysis.spectroscopy_analyses):
            ana.plotter(axs[int(i / columns), i % columns])

    def _plot_all_fit_q2(self, axs, columns):
        for i, ana in enumerate(self.q2_analysis.spectroscopy_analyses):
            ana.plotter(axs[int(i / columns), i % columns])

    def plot_spectroscopies(self, data_path: Path):
        """
        Plot all the spectroscopy analyses for both qubits and save the figures.
        """

        n_analyses = len(self.q1_analysis.spectroscopy_analyses)
        columns = int(np.ceil(np.sqrt(n_analyses)))
        rows = int(np.ceil(n_analyses / columns))
        fig, axs = create_figure_with_top_band(rows, columns)
        self._plot_all_fit_q1(axs, columns)

        full_path = (
            data_path
            / f"{self.name}_{self.coupler}_{self.name_qubit_1}_spectroscopies.png"
        )
        fig.savefig(full_path, bbox_inches="tight", dpi=300)

        fig, axs = create_figure_with_top_band(rows, columns)
        self._plot_all_fit_q2(axs, columns)

        full_path = (
            data_path
            / f"{self.name}_{self.coupler}_{self.name_qubit_2}_spectroscopies.png"
        )
        fig.savefig(full_path, bbox_inches="tight", dpi=300)


class QubitSpectroscopyVsCurrentNodeAnalysis(BaseAllCouplersAnalysis):
    """
    This class analyzes the qubit spectroscopy data as a function of the current for all coupler.
    """

    single_coupler_analysis_obj = QubitSpectroscopyVsCurrentCouplerAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def _save_other_plots(self):
        for c_ana in self.coupler_analyses:
            c_ana.plot_spectroscopies(self.data_path)


class ResonatorSpectroscopyVsCurrentNodeAnalysis(BaseAllCouplersAnalysis):
    """
    This class analyzes the resonator spectroscopy data as a function of the current for all coupler.
    """

    single_coupler_analysis_obj = ResonatorSpectroscopyVsCurrentCouplerAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def _save_other_plots(self):
        for c_ana in self.coupler_analyses:
            c_ana.plot_spectroscopies(self.data_path)
