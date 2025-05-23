# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023
# (C) Copyright Michele Faucci Giannelli 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from typing import List
from matplotlib import patches, pyplot as plt
import numpy as np

from tergite_autocalibration.lib.base.analysis import (
    BaseAllQubitsAnalysis,
    BaseQubitAnalysis,
)
from tergite_autocalibration.lib.base.utils.figure_util import (
    create_figure_with_top_band,
)
from tergite_autocalibration.lib.nodes.readout.resonator_spectroscopy.analysis import (
    ResonatorSpectroscopyQubitAnalysis,
)
from tergite_autocalibration.utils.dto.qoi import QOI


class PunchoutQubitAnalysis(BaseQubitAnalysis):
    """
    This class implements the punchout qubit analysis, which is used to
    measure the readout amplitude.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.amplitude_coord = None
        self.frequency_coord = None
        self.amplitudes = None
        self.frequencies = None
        self.last_good_freq = None
        self.best_amplitude = None
        self.detected_frequencies = []
        self.resonator_spectroscopy_analyses: List[
            ResonatorSpectroscopyQubitAnalysis
        ] = []
        self.shift_threshold = 0.02e6

    def analyse_qubit(self):
        """
        This method performs the analysis of the qubit data. It extracts the
        readout amplitude and frequency from the dataset and performs a
        resonator spectroscopy analysis for each amplitude. It then selects
        the best amplitude based on the detected resonator frequency.
        """

        for coord in self.dataset[self.data_var].coords:
            if "amplitudes" in coord:
                self.amplitude_coord = coord
            elif "frequencies" in coord:
                self.frequency_coord = coord

        self.amplitudes = self.dataset[self.amplitude_coord].values
        self.frequencies = self.dataset[self.frequency_coord].values

        magnitudes = self.magnitudes[self.data_var].values
        norm_magnitudes = magnitudes / np.max(magnitudes, axis=0)
        self.S21[f"y{self.qubit}"].values = norm_magnitudes

        for i, amplitude in enumerate(self.amplitudes):
            ds = self.dataset.sel({self.amplitude_coord: amplitude})

            res_spec_analysis = ResonatorSpectroscopyQubitAnalysis(self.name, "")
            resonator_frequency = res_spec_analysis.process_qubit(
                ds, self.data_var[1:]
            ).analysis_result["clock_freqs:readout"]["value"]

            self.detected_frequencies.append(resonator_frequency)
            self.resonator_spectroscopy_analyses.append(res_spec_analysis)

        for i, amplitude in enumerate(self.amplitudes):
            resonator_frequency = self.detected_frequencies[i]
            if np.isnan(resonator_frequency):
                continue

            if self.last_good_freq is None:
                self.last_good_freq = resonator_frequency
                self.best_amplitude = amplitude
                continue

            # Detect shift in resonator frequency
            if abs(resonator_frequency - self.last_good_freq) > self.shift_threshold:
                break  # Frequency shift detected — use last amplitude

            self.best_amplitude = amplitude
            self.last_good_freq = resonator_frequency

        analysis_succesful = True

        analysis_result = {
            "measure:pulse_amp": {
                "value": self.best_amplitude,
                "error": np.nan,
            }
        }

        qoi = QOI(analysis_result, analysis_succesful)

        return qoi

    def plotter(self, ax: plt.Axes):
        """
        This method plots the results of the analysis. It creates a 2D
        scatter plot of the detected resonator frequencies against the
        readout pulse amplitudes. It also highlights the best amplitude
        with a red cross and adds a colorbar indicating the normalized
        |S21| values.
        """

        cax = self.S21[self.data_var].plot(ax=ax, x=self.amplitude_coord)
        ax.scatter(
            self.detected_frequencies,
            self.amplitudes,
            c="b",
            label="Fitted resonator freq.",
            marker="o",
        )
        ax.scatter(
            self.best_amplitude,
            self.last_good_freq,
            c="r",
            label=f"Amplitude = {self.best_amplitude:.3f}",
            marker="X",
            s=200,
            edgecolors="k",
            linewidth=1.5,
            zorder=10,
        )
        ax.set_ylabel("Resonator frequency [Hz]")
        ax.set_xlabel("Readout pulse amplitude [V?]")

        cbar = cax.colorbar  # Only add colorbar if it's an image or similar plot
        cbar.set_label(
            "Normalized |S21|", rotation=270, labelpad=15
        )  # Custom label here

        ax.legend()  # Add legend to the plot

    def plot_spectroscopies(self, data_path):
        """
        This method creates a figure with subplots for each resonator
        spectroscopy analysis. It highlights the best amplitude with a red
        rectangle around the corresponding subplot.
        """

        n_analyses = len(self.resonator_spectroscopy_analyses)
        ncols = 4
        nrows = int(np.ceil(n_analyses / ncols))

        fig, axs = create_figure_with_top_band(nrows, ncols)

        selected_index = -1
        for i, ana in enumerate(self.resonator_spectroscopy_analyses):
            ana.plotter(axs[int(i / ncols), i % ncols])
            if self.best_amplitude == self.amplitudes[i]:
                selected_index = i

        row = selected_index // ncols
        col = selected_index % ncols
        ax = axs[row, col]

        # Add a red rectangle around the entire axes
        rect = patches.Rectangle(
            (0, 0),
            1,
            1,
            transform=ax.transAxes,
            linewidth=3,
            edgecolor="red",
            facecolor="none",
            zorder=20,
        )
        ax.add_patch(rect)

        full_path = data_path / f"{self.name}_{self.qubit}_spectroscopies.png"
        fig.savefig(full_path, bbox_inches="tight", dpi=200)


class PunchoutNodeAnalysis(BaseAllQubitsAnalysis):
    """
    This class implements the punchout node analysis, which is used to
    measure the readout amplitude.
    """

    single_qubit_analysis_obj = PunchoutQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def _save_other_plots(self):
        for q_ana in self.qubit_analyses:
            q_ana.plot_spectroscopies(self.data_path)
