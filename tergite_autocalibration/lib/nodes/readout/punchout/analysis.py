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


class PunchoutAnalysis(BaseQubitAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.amplitude_coord = None
        self.frequency_coord = None
        self.last_good_freq = None
        self.best_amplitude = None
        self.detected_frequencies = []
        self.resonator_spectroscopy_analyses = []
        self.shift_threshold = 0.1e6

    def analyse_qubit(self):
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
            resonator_frequency = res_spec_analysis.setup_qubit_and_analyze(
                ds, self.data_var[1:]
            ).analysis_result["clock_freqs:readout"]["value"]

            if np.isnan(resonator_frequency):
                continue

            self.resonator_spectroscopy_analyses.append(res_spec_analysis)
            self.detected_frequencies.append(resonator_frequency)

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

    def plotter(self, axis: plt.Axes):
        cax = self.S21[self.data_var].plot(ax=axis, x=self.amplitude_coord)
        axis.scatter(
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
        axis.set_ylabel("Resonator frequency [Hz]")
        axis.set_xlabel("Readout pulse amplitude [V?]")

        cbar = cax.colorbar  # Only add colorbar if it's an image or similar plot
        cbar.set_label(
            "Normalized |S21|", rotation=270, labelpad=15
        )  # Custom label here

        axis.legend()  # Add legend to the plot

    def plot_spectroscopies(self, data_path):
        n_analyses = len(self.resonator_spectroscopy_analyses)
        nrows = int(np.ceil(n_analyses / 4))
        ncols = 4

        fig, axs = create_figure_with_top_band(nrows, ncols)

        selected_index = -1
        for i, ana in enumerate(self.resonator_spectroscopy_analyses):
            ana.plotter(axs[int(i / 4), i % 4])
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
    single_qubit_analysis_obj = PunchoutAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def save_other_plots(self):
        for q_ana in self.qubit_analyses:
            q_ana.plot_spectroscopies(self.data_path)
