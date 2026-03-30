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
from scipy.signal import find_peaks

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


class CouplerSpectroscopyAnalysis(BaseCouplerAnalysis):
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
    ):
        crossing_currents = []

        # TODO: add a gradient check
        (frequency_jumps,) = np.where(np.abs(np.diff(frequencies)) > threshold)
        for jump in frequency_jumps:
            crossing_current = np.mean((currents[jump], currents[jump + 1]))
            crossing_currents.append(crossing_current)

        return crossing_currents

    def detect_peaks(self, qubit_specs_dataarray: xarray.DataArray):
        for coord in qubit_specs_dataarray.coords:
            coord = str(coord)
            if "frequencies" in coord:
                frequency_coord = coord
                break
        detected_frequencies = []
        detected_currents = []
        for current in self.dc_currents:
            array = qubit_specs_dataarray.sel({self.current_coord: current})
            noise_level = array.std().item()
            peak, _ = find_peaks(array, prominence=3 * noise_level)
            if peak.size != 1:
                continue
            qubit_frequency = array[frequency_coord].values[peak].item()
            detected_frequencies.append(qubit_frequency)
            detected_currents.append(current)
        return detected_frequencies, detected_currents

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

        # split the qubit from the resonator spectroscopies
        control_qubit_spectroscopy = control_magnitudes.where(
            control_magnitudes[self.control_qubit_frequencies_coord].notnull(),
            drop=True,
        )
        # control_resonator_spectroscopy = control_magnitudes.where(
        #     control_magnitudes[self.control_resonator_frequencies_coord].notnull(),
        #     drop=True,
        # )
        target_qubit_spectroscopy = target_magnitudes.where(
            target_magnitudes[self.target_qubit_frequencies_coord].notnull(),
            drop=True,
        )
        # target_resonator_spectroscopy = target_magnitudes.where(
        #     target_magnitudes[self.target_resonator_frequencies_coord].notnull(),
        #     drop=True,
        # )

        # clean up dimensions
        self.control_qubit_spectroscopy = control_qubit_spectroscopy.swap_dims(
            {self.control_common_dim: self.control_qubit_frequencies_coord}
        )
        # ).drop_vars(self.control_resonator_frequencies_coord)
        # self.control_resonator_spectroscopy = control_resonator_spectroscopy.swap_dims(
        #     {self.control_common_dim: self.control_resonator_frequencies_coord}
        # ).drop_vars(self.control_qubit_frequencies_coord)
        self.target_qubit_spectroscopy = target_qubit_spectroscopy.swap_dims(
            {self.target_common_dim: self.target_qubit_frequencies_coord}
        )
        # ).drop_vars(self.target_resonator_frequencies_coord)
        # self.target_resonator_spectroscopy = target_resonator_spectroscopy.swap_dims(
        #     {self.target_common_dim: self.target_resonator_frequencies_coord}
        # ).drop_vars(self.target_qubit_frequencies_coord)

        (
            self.control_qubit_detected_frequencies,
            self.control_qubit_detected_currents,
        ) = self.detect_peaks(control_qubit_spectroscopy)
        self.target_qubit_detected_frequencies, self.target_qubit_detected_currents = (
            self.detect_peaks(target_qubit_spectroscopy)
        )

        self.resonator_crossing_points = []
        self.control_crossing_currents = self._find_crossing_currents(
            self.control_qubit_detected_currents,
            self.control_qubit_detected_frequencies,
        )
        self.target_crossing_currents = self._find_crossing_currents(
            self.target_qubit_detected_currents,
            self.target_qubit_detected_frequencies,
        )

        analysis_succesful = True
        analysis_result = {
            "control_qubit_crossing_points": {
                "value": 0,
                # "value": self.control_crossing_currents,
                "error": 0,
            },
            "target_qubit_crossing_points": {
                "value": 0,
                # "value": self.target_crossing_currents,
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
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2)
        self.control_qubit_spectroscopy.plot(ax=ax1, x=self.current_coord)
        self.target_qubit_spectroscopy.plot(ax=ax2, x=self.current_coord)
        # self.control_resonator_spectroscopy.plot(ax=ax3, x=self.current_coord)
        # self.target_resonator_spectroscopy.plot(ax=ax4, x=self.current_coord)

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


class CouplerSpectroscopyNodeAnalysis(BaseAllCouplersAnalysis):
    """
    This class analyzes the qubit spectroscopy data as a function of the current for all coupler.
    """

    single_coupler_analysis_obj = CouplerSpectroscopyAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
