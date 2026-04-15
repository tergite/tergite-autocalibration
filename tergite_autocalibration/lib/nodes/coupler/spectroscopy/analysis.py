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


from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
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
    ResonatorAvoidedCrossings,
    resonator_hanger_frequency,
)
from tergite_autocalibration.utils.dto.qoi import QOI


class CouplerSpectroscopyAnalysis(BaseCouplerAnalysis):
    """
    This class analyzes the qubit spectroscopy data as a function of the current for a coupler.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.model = fm.ResonatorModel()

    def find_peaks(self, spectroscopy_dataarray: xr.DataArray):
        qubit = spectroscopy_dataarray.qubit
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

        role = "control" if self.control_qubit == qubit else "target"
        n_freqs = len(detected_frequencies)

        coords = {
            "obs": range(n_freqs),
            "role": ("obs", [role] * n_freqs),
            "mode": ("obs", ["qubit"] * n_freqs),
        }

        df = xr.DataArray(detected_frequencies, coords=coords, dims="obs")
        dc = xr.DataArray(detected_currents, coords=coords, dims="obs")

        ds = xr.Dataset({"frequencies": df, "currents": dc}).set_index(
            obs=["role", "mode"]
        )
        return ds

    def find_resonator_dips(self, spectroscopy_dataarray: xr.DataArray):
        qubit = spectroscopy_dataarray.qubit
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
            guess = self.model.guess(array, f=frequencies)
            fit = self.model.fit(array, params=guess, f=frequencies)
            fit_fr = fit.params["fr"].value
            fit_Ql = fit.params["Ql"].value
            fit_Qe = fit.params["Qe"].value
            fit_ph = fit.params["theta"].value
            resonator_frequency = resonator_hanger_frequency(
                fit_fr=fit_fr, fit_ph=fit_ph, fit_Qe=fit_Qe, fit_Ql=fit_Ql
            )
            detected_frequencies.append(resonator_frequency)
            detected_currents.append(current)

        role = "control" if self.control_qubit == qubit else "target"
        n_freqs = len(detected_frequencies)
        coords = {
            "obs": range(n_freqs),
            "role": ("obs", [role] * n_freqs),
            "mode": ("obs", ["qubit"] * n_freqs),
        }
        df = xr.DataArray(detected_frequencies, coords=coords, dims="obs")
        dc = xr.DataArray(detected_currents, coords=coords, dims="obs")

        ds = xr.Dataset({"frequencies": df, "currents": dc}).set_index(
            obs=["role", "mode"]
        )
        return ds

    def _prepare_spectroscopy(self, data, freq_coord, common_dim, drop_coord):
        return (
            data.where(data[freq_coord].notnull(), drop=True)
            .swap_dims({common_dim: freq_coord})
            .drop_vars(drop_coord)
        )

    def remove_none(self, seq: Sequence):
        values = [x for x in seq if x is not None]
        return values

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

        control_attrs = self.control_qubit_data_var.attrs
        target_attrs = self.target_qubit_data_var.attrs
        control_magnitudes = xr.ufuncs.abs(self.control_qubit_data_var).assign_attrs(
            control_attrs
        )
        target_magnitudes = xr.ufuncs.abs(self.target_qubit_data_var).assign_attrs(
            target_attrs
        )

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
        self.control_peaks = self.find_peaks(self.control_qubit_spectroscopy)
        self.target_peaks = self.find_peaks(self.target_qubit_spectroscopy)

        # Collect resonator spectroscopy dips
        self.control_dips = self.find_resonator_dips(
            self.control_resonator_spectroscopy
        )
        self.target_dips = self.find_resonator_dips(self.target_resonator_spectroscopy)

        control_crossings = AvoidedCrossings(
            self.control_peaks.currents, self.control_peaks.frequencies
        )
        target_crossings = AvoidedCrossings(
            self.target_peaks.currents, self.target_peaks.frequencies
        )
        target_res_crossings = ResonatorAvoidedCrossings(
            self.target_dips.currents, self.target_dips.frequencies
        )
        control_res_crossings = ResonatorAvoidedCrossings(
            self.control_dips.currents, self.control_dips.frequencies
        )

        self.control_cross_currents = control_crossings.crossing_currents
        self.control_cross_frequency = control_crossings.crossing_frequency.value
        self.control_cross_freq_above = control_crossings.crossing_frequency.above
        self.control_cross_freq_below = control_crossings.crossing_frequency.below
        self.target_cross_currents = target_crossings.crossing_currents
        self.target_cross_frequency = target_crossings.crossing_frequency.value
        self.target_cross_freq_above = target_crossings.crossing_frequency.above
        self.target_cross_freq_below = target_crossings.crossing_frequency.below
        self.control_res_cross_currents = control_res_crossings.crossing_currents
        self.control_res_cross_frequency = control_res_crossings.crossing_frequency
        self.target_res_cross_currents = target_res_crossings.crossing_currents
        self.target_res_cross_frequency = target_res_crossings.crossing_frequency

        crossing_points = []
        for cross_current in self.control_cross_currents:
            crossing_points.append((cross_current, self.control_cross_frequency))
        for cross_current in self.target_cross_currents:
            crossing_points.append((cross_current, self.target_cross_frequency))
        for cross_current in self.control_res_cross_currents:
            crossing_points.append((cross_current, self.control_res_cross_frequency))
        for cross_current in self.target_res_cross_currents:
            crossing_points.append((cross_current, self.target_res_cross_frequency))
        self.crossing_points = crossing_points

        hint_Ic_res_target = target_res_crossings.I0_hint
        hint_Ic_res_control = control_res_crossings.I0_hint
        hint_Ic_qub_target = target_crossings.Ic_hint
        hint_Ic_qub_control = control_crossings.Ic_hint
        hint_I0_target = target_crossings.I0_hint
        hint_I0_control = control_crossings.I0_hint

        res_Ic_hints = self.remove_none((hint_Ic_res_control, hint_Ic_res_target))
        qub_Ic_hints = self.remove_none((hint_Ic_qub_control, hint_Ic_qub_target))
        qub_I0_hints = self.remove_none((hint_I0_control, hint_I0_target))
        if res_Ic_hints:
            Ic_hint = np.mean(res_Ic_hints)
        elif qub_Ic_hints:
            Ic_hint = np.mean(qub_Ic_hints)
        else:
            Ic_hint = None

        if qub_I0_hints:
            I0_hint = np.mean(qub_I0_hints)
        else:
            I0_hint = None

        cross_currents, cross_freqs = zip(*crossing_points)
        self.coupler_model = CouplerModel()
        if Ic_hint:
            self.coupler_model.set_param_hint("Ic", value=Ic_hint, vary=True)
        if I0_hint:
            self.coupler_model.set_param_hint("I0", value=I0_hint, vary=True)
        self.coupler_result = self.coupler_model.fit(
            cross_freqs, current=cross_currents
        )
        coupler_model_values = self.coupler_result.best_values
        fmax = coupler_model_values["fmax"]
        Ic = coupler_model_values["Ic"]
        I0 = coupler_model_values["I0"]
        offset = coupler_model_values["offset"]

        analysis_succesful = True
        analysis_result = {
            "fmax": {"value": fmax, "error": 0},
            "Ic": {"value": Ic, "error": 0},
            "I0": {"value": I0, "error": 0},
            "offset": {"value": offset, "error": 0},
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

        control_resonator_magnitudes = xr.ufuncs.abs(
            self.control_resonator_spectroscopy
        )
        target_resonator_magnitudes = xr.ufuncs.abs(self.target_resonator_spectroscopy)
        figures_list = []
        fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2)
        self.control_qubit_spectroscopy.plot(ax=ax1, x=self.current_coord)
        self.target_qubit_spectroscopy.plot(ax=ax2, x=self.current_coord)
        control_resonator_magnitudes.plot(ax=ax3, x=self.current_coord)
        target_resonator_magnitudes.plot(ax=ax4, x=self.current_coord)

        peak_styles = {"s": 52, "c": "red"}
        coupler_styles = {"s": 52, "c": "red", "edgecolors": "black"}
        crossing_styles = {
            "color": "orange",
            "gapcolor": "black",
            "linestyle": "dashed",
            "linewidth": 2,
        }
        edge_styles = {"color": "grey", "linestyle": "dashed", "linewidth": 2}

        for cross_current in self.control_cross_currents:
            ax1.axvline(cross_current, **crossing_styles)
        for cross_current in self.target_cross_currents:
            ax2.axvline(cross_current, **crossing_styles)
        for cross_current in self.control_res_cross_currents:
            ax3.axvline(cross_current, **crossing_styles)
        for cross_current in self.target_res_cross_currents:
            ax4.axvline(cross_current, **crossing_styles)

        ax1.set(xlabel=None)
        ax2.set(xlabel=None)

        fit_plot_currents = np.linspace(self.dc_currents[0], self.dc_currents[-1], 200)
        evaluated_freqs = self.coupler_model.eval(
            self.coupler_result.params, current=fit_plot_currents
        )
        ax5.plot(fit_plot_currents, evaluated_freqs, "r-")
        fmax = (
            self.coupler_result.best_values["fmax"]
            + self.coupler_result.best_values["offset"]
        )

        cross_currents, cross_freqs = zip(*self.crossing_points)
        ax5.scatter(cross_currents, cross_freqs, **coupler_styles)

        scatter_plots = [
            (ax1, self.control_peaks.currents, self.control_peaks.frequencies),
            (ax2, self.target_peaks.currents, self.target_peaks.frequencies),
            (ax3, self.control_dips.currents, self.control_dips.frequencies),
            (ax4, self.target_dips.currents, self.target_dips.frequencies),
        ]

        for ax, x, y in scatter_plots:
            if x is not None and y is not None:
                ax.scatter(x, y, **peak_styles)

        horizontal_lines = [
            (ax1, self.control_cross_freq_above, edge_styles),
            (ax1, self.control_cross_freq_below, edge_styles),
            (ax1, self.control_cross_frequency, crossing_styles),
            (ax2, self.target_cross_freq_above, edge_styles),
            (ax2, self.target_cross_freq_below, edge_styles),
            (ax2, self.target_cross_frequency, crossing_styles),
            (ax5, fmax, crossing_styles),
        ]
        for ax, freq, style in horizontal_lines:
            if freq is not None:
                ax.axhline(freq, **style)
        ax5.axhline(fmax, **crossing_styles, label=f"fmax: {fmax:.4e}")
        ax5.set_ylabel('frequencies')
        ax5.legend()
        for ax in (ax1, ax2, ax3, ax4, ax5):
            plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment="center")

        ax6.axis("off")

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
