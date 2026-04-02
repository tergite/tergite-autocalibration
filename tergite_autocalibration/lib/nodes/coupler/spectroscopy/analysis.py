# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024, 2025, 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


import matplotlib.pyplot as plt
import numpy as np
import xarray
from quantify_core.analysis import fitting_models as fm
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
from scipy.stats import median_abs_deviation

from tergite_autocalibration.lib.base.analysis import (
    BaseAllCouplersAnalysis,
    BaseCouplerAnalysis,
)
from tergite_autocalibration.lib.utils.analysis_models import (
    AvoidedCrossings,
    CouplerModel,
    resonator_hanger_frequency,
)
from tergite_autocalibration.utils.dto.qoi import QOI

model = fm.ResonatorModel()


class CouplerSpectroscopyAnalysis(BaseCouplerAnalysis):
    """
    This class analyzes the qubit spectroscopy data as a function of the current for a coupler.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def find_peaks(self, spectroscopy_dataarray: xarray.DataArray):
        for coord in spectroscopy_dataarray.coords:
            coord = str(coord)
            if "frequencies" in coord:
                frequency_coord = coord
                break
        detected_frequencies = []
        detected_currents = []
        for current in self.dc_currents:
            array = spectroscopy_dataarray.sel({self.current_coord: current})
            smoothed = gaussian_filter1d(array, sigma=2)
            # Using median deviation as it is more robust to outliers compared to std
            noise_level = median_abs_deviation(smoothed)
            peak, _ = find_peaks(smoothed, prominence=10 * noise_level)
            if peak.size != 1:
                continue
            qubit_frequency = array[frequency_coord].values[peak].item()
            detected_frequencies.append(qubit_frequency)
            detected_currents.append(current)
        return detected_frequencies, detected_currents

    def find_resonator_dips(self, spectroscopy_dataarray: xarray.DataArray):
        for coord in spectroscopy_dataarray.coords:
            coord = str(coord)
            if "frequencies" in coord:
                frequency_coord = coord
                frequencies = spectroscopy_dataarray.coords[coord].values
                break
        detected_frequencies = []
        detected_currents = []
        for current in self.dc_currents:
            array = spectroscopy_dataarray.sel({self.current_coord: current})
            guess = model.guess(array, f=frequencies)
            fit = model.fit(array, params=guess, f=frequencies)
            fit_fr = fit.params["fr"].value
            fit_Ql = fit.params["Ql"].value
            fit_Qe = fit.params["Qe"].value
            fit_ph = fit.params["theta"].value
            resonator_frequency = resonator_hanger_frequency(
                fit_fr=fit_fr, fit_ph=fit_ph, fit_Qe=fit_Qe, fit_Ql=fit_Ql
            )
            detected_frequencies.append(resonator_frequency)
            detected_currents.append(current)
        return detected_frequencies, detected_currents

    def _prepare_spectroscopy(self, data, freq_coord, common_dim, drop_coord):
        return (
            data.where(data[freq_coord].notnull(), drop=True)
            .swap_dims({common_dim: freq_coord})
            .drop_vars(drop_coord)
        )

    def analyze_coupler(self):
        for coord_name in self.dataset.coords:
            coord_name = str(coord_name)
            coord = self.dataset[coord_name]
            if "currents" in coord_name:
                self.current_coord = coord_name
                self.dc_currents = coord.values
        for coord_name in self.control_qubit_data_var.coords:
            coord_name = str(coord_name)
            if "qubit_frequencies" in coord_name:
                self.control_qubit_frequencies_coord = coord_name
            elif "resonator_frequencies" in coord_name:
                self.control_resonator_frequencies_coord = coord_name
        for coord_name in self.target_qubit_data_var.coords:
            coord_name = str(coord_name)
            if "qubit_frequencies" in coord_name:
                self.target_qubit_frequencies_coord = coord_name
            elif "resonator_frequencies" in coord_name:
                self.target_resonator_frequencies_coord = coord_name
        for dim in self.control_qubit_data_var.dims:
            if "common_dimension" in dim:
                self.control_common_dim = dim
        for dim in self.target_qubit_data_var.dims:
            if "common_dimension" in dim:
                self.target_common_dim = dim

        control_magnitudes = xarray.ufuncs.abs(self.control_qubit_data_var)
        target_magnitudes = xarray.ufuncs.abs(self.target_qubit_data_var)

        configs = {
            "control_qubit_spectroscopy": (
                control_magnitudes,
                self.control_qubit_frequencies_coord,
                self.control_common_dim,
                self.control_resonator_frequencies_coord,
            ),
            "control_resonator_spectroscopy": (
                self.control_qubit_data_var,
                self.control_resonator_frequencies_coord,
                self.control_common_dim,
                self.control_qubit_frequencies_coord,
            ),
            "target_qubit_spectroscopy": (
                target_magnitudes,
                self.target_qubit_frequencies_coord,
                self.target_common_dim,
                self.target_resonator_frequencies_coord,
            ),
            "target_resonator_spectroscopy": (
                self.target_qubit_data_var,
                self.target_resonator_frequencies_coord,
                self.target_common_dim,
                self.target_qubit_frequencies_coord,
            ),
        }
        for attr, (data, freq, dim, drop) in configs.items():
            setattr(self, attr, self._prepare_spectroscopy(data, freq, dim, drop))

        # Collect qubit spectroscopy peaks
        (
            self.control_qubit_detected_frequencies,
            self.control_qubit_detected_currents,
        ) = self.find_peaks(self.control_qubit_spectroscopy)
        self.target_qubit_detected_frequencies, self.target_qubit_detected_currents = (
            self.find_peaks(self.target_qubit_spectroscopy)
        )
        # Collect resonator spectroscopy dips
        (
            self.control_resonator_detected_frequencies,
            self.control_resonator_detected_currents,
        ) = self.find_resonator_dips(self.control_resonator_spectroscopy)
        (
            self.target_resonator_detected_frequencies,
            self.target_resonator_detected_currents,
        ) = self.find_resonator_dips(self.target_resonator_spectroscopy)

        self.control_resonator_magnitudes = xarray.ufuncs.abs(
            self.control_resonator_spectroscopy
        )
        self.target_resonator_magnitudes = xarray.ufuncs.abs(
            self.target_resonator_spectroscopy
        )

        self.resonator_crossing_points = []

        control_crossings = AvoidedCrossings(
            self.control_qubit_detected_currents,
            self.control_qubit_detected_frequencies,
        )
        self.control_crossing_currents = control_crossings.crossing_currents
        (
            self.control_crossing_frequency,
            self.control_crossing_frequency_below,
            self.control_crossing_frequency_above,
        ) = control_crossings.crossing_frequency

        target_crossings = AvoidedCrossings(
            self.target_qubit_detected_currents,
            self.target_qubit_detected_frequencies,
        )
        self.target_crossing_currents = target_crossings.crossing_currents
        (
            self.target_crossing_frequency,
            self.target_crossing_frequency_below,
            self.target_crossing_frequency_above,
        ) = target_crossings.crossing_frequency

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

    def plotter(self, figures_dictionary: dict[str, list]):
        """
        Create the anticrossing figures and populate the figures dictionary.
        Args:
             figures_dictionary: A reference to the figures dictionary that the base
             analysis plots the key is the coupler labe and the value is a list
             containing the anticrossing figure for that coupler
        """
        figures_list = []
        fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2)
        self.control_qubit_spectroscopy.plot(ax=ax1, x=self.current_coord)
        self.target_qubit_spectroscopy.plot(ax=ax2, x=self.current_coord)
        self.control_resonator_magnitudes.plot(ax=ax3, x=self.current_coord)
        self.target_resonator_magnitudes.plot(ax=ax4, x=self.current_coord)

        peak_styles = {"s": 52, "c": "red"}
        crossing_styles = {"color": "orange", "linestyle": "dashed", "linewidth": 2}
        edge_styles = {"color": "grey", "linestyle": "dashed", "linewidth": 2}

        crossing_points = []
        for cross_current in self.control_crossing_currents:
            ax1.axvline(cross_current, **crossing_styles)
            crossing_points.append((cross_current, self.control_crossing_frequency))
        for cross_current in self.target_crossing_currents:
            ax2.axvline(cross_current, **crossing_styles)
            crossing_points.append((cross_current, self.target_crossing_frequency))
        crossing_points.append((0, 6.63189e9))
        crossing_points.append((6.83e-4, 6.63189e9))

        cross_currents, cross_freqs = zip(*crossing_points)
        coupler_model = CouplerModel()
        coupler_result = coupler_model.fit(cross_freqs, current=cross_currents)
        coupler_result.plot_fit(ax5, numpoints=200, xlabel=None, title=None)

        ax5.legend()

        plots = [
            (
                ax1,
                self.control_qubit_detected_currents,
                self.control_qubit_detected_frequencies,
            ),
            (
                ax2,
                self.target_qubit_detected_currents,
                self.target_qubit_detected_frequencies,
            ),
            (
                ax3,
                self.control_resonator_detected_currents,
                self.control_resonator_detected_frequencies,
            ),
            (
                ax4,
                self.target_resonator_detected_currents,
                self.target_resonator_detected_frequencies,
            ),
            (ax5, cross_currents, cross_freqs),
        ]

        for ax, x, y in plots:
            if x is not None and y is not None:
                ax.scatter(x, y, **peak_styles)

        horizontal_lines = [
            (ax1, self.control_crossing_frequency_above, edge_styles),
            (ax1, self.control_crossing_frequency_below, edge_styles),
            (ax1, self.control_crossing_frequency, crossing_styles),
            (ax2, self.target_crossing_frequency_above, edge_styles),
            (ax2, self.target_crossing_frequency_below, edge_styles),
            (ax2, self.target_crossing_frequency, crossing_styles),
        ]
        ax6.axis("off")

        for ax, freq, style in horizontal_lines:
            if freq is not None:
                ax.axhline(freq, **style)

        figures_list.append(fig)
        figures_dictionary[self.coupler] = figures_list
        plt.show()
        return


class CouplerSpectroscopyNodeAnalysis(BaseAllCouplersAnalysis):
    """
    This class analyzes the qubit spectroscopy data as a function of the current for all coupler.
    """

    single_coupler_analysis_obj = CouplerSpectroscopyAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
