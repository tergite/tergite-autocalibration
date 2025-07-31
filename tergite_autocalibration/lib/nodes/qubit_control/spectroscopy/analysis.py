# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Michele Faucci Giannelli 2024
# (C) Copyright Joel Sandås 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Module containing classes that model, fit and plot data
from a qubit (two tone) spectroscopy experiment.
"""
import numpy as np
import xarray as xr
from lmfit.models import LorentzianModel
from scipy import signal

from tergite_autocalibration.lib.base.analysis import (
    BaseAllQubitsAnalysis,
    BaseQubitAnalysis,
)
from tergite_autocalibration.utils.dto.qoi import QOI
from tergite_autocalibration.utils.logging import logger


# TODO: this is flagged for removal
class QubitSpectroscopyAnalysis(BaseQubitAnalysis):
    """
    Analysis that fits a Lorentzian function to qubit spectroscopy data.
    The resulting fit can be analyzed to determine if a peak was found or not.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.fit_results = {}

    def _analyse_spectroscopy(self):
        # Fetch the resulting measurement variables
        for coord in self.dataset[self.data_var].coords:
            if "frequencies" in coord:
                self.frequencies = coord
            elif "currents" in coord:
                self.currents = coord

        self.frequencies_value = self.dataset[self.frequencies].values

        self.fit_freqs = np.linspace(
            self.frequencies_value[0], self.frequencies_value[-1], 500
        )  # x-values for plotting

        # Initialize the Lorentzian model
        model = LorentzianModel()

        # Gives an initial guess for the model parameters and then fits the model to the data.
        guess = model.guess(
            self.magnitudes.to_dataarray().values.flatten(), x=self.frequencies_value
        )
        fit_result = model.fit(
            self.magnitudes.to_dataarray().values.flatten(),
            params=guess,
            x=self.frequencies_value,
        )

        self.freq = fit_result.params["center"].value
        self.uncertainty = fit_result.params["center"].stderr

        self.fit_y = model.eval(
            fit_result.params, **{model.independent_vars[0]: self.fit_freqs}
        )

    def analyse_qubit(self):
        self._analyse_spectroscopy()
        analysis_successful = True
        analysis_result = {
            "clock_freqs:f01": {
                "value": self.freq,
                "error": self.uncertainty,
            },
        }
        qoi = QOI(analysis_result, analysis_successful)
        return qoi

    def reject_outliers(self, data, m=3.0):
        # Filters out datapoints in data that deviate too far from the median
        shifted_data = np.abs(data - np.median(data))
        mdev = np.median(shifted_data)
        s = shifted_data / mdev if mdev else np.zeros(len(shifted_data))
        filtered_data = data[s < m]
        return filtered_data

    def has_peak(
        self, prom_coef: float = 6, wid_coef: float = 2.4, outlier_median: float = 3.0
    ):
        # Determines if the data contains one distinct peak or only noise
        x_dataarray = self.magnitudes.to_dataarray()
        x = x_dataarray.values[0]
        x_filtered = self.reject_outliers(x, outlier_median)
        self.filtered_std = np.std(x_filtered)
        peaks, properties = signal.find_peaks(
            x, prominence=self.filtered_std * prom_coef, width=wid_coef
        )
        self.prominence = (
            properties["prominences"][0] if len(properties["prominences"]) == 1 else 0
        )
        self.hasPeak = peaks.size == 1
        self.hasPeak = True
        return self.hasPeak

    def plotter(self, ax):
        # Plots the data and the fitted model of a qubit spectroscopy experiment
        if self.hasPeak:
            ax.plot(self.fit_freqs, self.fit_y, "r-", lw=3.0)
            min = np.min(self.magnitudes)

            ax.plot(
                self.fit_freqs,
                self.fit_y,
                "r-",
                lw=3.0,
                label=f"freq = {self.freq:.6E} (Hz)",
            )

        x_dataarray = self.magnitudes.to_dataarray()
        x = x_dataarray.values[0].flatten
        ax.plot(self.frequencies_value, x, "bo-", ms=3.0)
        ax.set_title(f"Qubit Spectroscopy for {self.qubit}")
        ax.set_xlabel("frequency (Hz)")
        ax.set_ylabel("|S21| (V)")
        ax.grid()


class QubitSpectroscopyMaxThresholdQubitAnalysis(BaseQubitAnalysis):
    """
    Analysis that finds the maximum value in qubit spectroscopy data.
    """

    SIGNIFICANCE_THRESHOLD = 2.7

    def __init__(self, name, redis_fields, current):
        super().__init__(name, redis_fields)
        self.analysis_results = {}
        self.is_bad_value = False
        self.current = current

    def _analyse_spectroscopy(self):
        for coord in self.dataset[self.data_var].coords:
            if "frequencies" in coord:
                self.frequencies = coord

        self.frequencies_value = self.dataset[self.frequencies].values

        magnitudes = self.magnitudes.to_dataarray().values.flatten()
        self.max_value = np.max(magnitudes)
        self.max_index = np.argmax(magnitudes)

        mean_value = np.mean(magnitudes)
        std_value = np.std(magnitudes)

        self.max_significance = abs((self.max_value - mean_value) / std_value)

        if self.max_significance < self.SIGNIFICANCE_THRESHOLD:
            self.is_bad_value = True
            logger.warning(
                "This spectroscopy doeas not have a proper maximum, it is ok if this is in a transition region in the coupler spectroscopy"
            )
            self.freq = 0
        else:
            self.freq = self.frequencies_value[self.max_index]
        self.uncertainty = None

    def analyse_qubit(self):
        self._analyse_spectroscopy()
        analysis_successful = True
        analysis_result = {
            "clock_freqs:f01": {
                "value": self.freq,
                "error": self.uncertainty,
            },
        }
        qoi = QOI(analysis_result, analysis_successful)
        return qoi

    def plotter(self, ax):
        x_dataarray = self.magnitudes.to_dataarray()
        x = x_dataarray.values.flatten()

        ax.plot(self.frequencies_value, x, "bo-", ms=1.5, lw=0.8)

        if not self.is_bad_value:
            ax.axvline(
                self.freq,
                color="r",
                linestyle="--",
                label=f"Current: {self.current*1000:.2f}[mA]\nMax @ {self.max_significance:.1f}",
            )

        if self.is_bad_value:
            ax.scatter(
                self.frequencies_value[self.max_index],
                self.max_value,
                color="red",
                marker="x",
                s=100,
                linewidth=2,
                label=f"Current: {self.current*1000:.1f}[mA]\nMax @ {self.max_significance:.1f}",
            )

        ax.set_title(f"Qubit Spectroscopy for {self.qubit}", fontsize=8)
        ax.set_xlabel("Frequency (Hz)", fontsize=6)
        ax.set_ylabel("|S21| (V)", fontsize=6)

        ax.legend(fontsize=6, loc="upper right")
        ax.grid()


class QubitSpectroscopyMultidimAnalysis(BaseQubitAnalysis):
    """
    Analysis that fits a Lorentzian function to qubit spectroscopy data.
    The resulting fit can be analyzed to determine if a peak was found or not.
    """

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def _analyse_spectroscopy(self):
        for coord in self.dataset[self.data_var].coords:
            if "frequencies" in coord:
                self.frequency_coords = coord
                self.frequencies = self.dataset.coords[coord].values
            elif "amplitudes" in coord:
                self.amplitude_coords = coord
                self.amplitudes = self.dataset.coords[coord].values

        self.spec_ampl = 0
        self.qubit_ampl = 0
        self.qubit_freq = 0
        if hasattr(self, "amplitudes"):
            for i, a in enumerate(self.amplitudes):
                if isinstance(self.magnitudes, xr.Dataset):
                    data_var_name = list(self.S21.data_vars.keys())[
                        0
                    ]  # Adjust if specific variable name is known
                    s21_dataarray = self.magnitudes[data_var_name]
                else:
                    raise TypeError("Expected self.S21 to be an xarray.DataArray")
                s21_values = s21_dataarray.values

                these_magnitudes = s21_values[i]
                if not self.has_peak(these_magnitudes):
                    continue

                qubit_freq = self.frequencies[these_magnitudes.argmax()]
                qubit_ampl = these_magnitudes.max()
                if qubit_ampl > self.qubit_ampl:
                    self.qubit_ampl = qubit_ampl
                    self.qubit_freq = qubit_freq
                    self.spec_ampl = a

        else:
            if self.has_peak(self.magnitudes):
                self.qubit_freq = self.frequencies[self.magnitudes.argmax()]

    def analyse_qubit(self):
        self._analyse_spectroscopy()
        analysis_successful = True
        analysis_result = {
            "clock_freqs:f01": {
                "value": self.qubit_freq,
                "error": 0,
            },
            "spec:spec_ampl_optimal": {
                "value": self.spec_ampl,
                "error": 0,
            },
        }
        qoi = QOI(analysis_result, analysis_successful)
        return qoi

    def reject_outliers(self, x, m=3.0):
        # Filters out datapoints in x that deviate too far from the median
        d = np.abs(x - np.median(x))
        mdev = np.median(d)
        s = d / mdev if mdev else np.zeros(len(d))
        return x[s < m]

    def has_peak(
        self,
        x,
        prom_coef: float = 7,
        wid_coef: float = 2.4,
        outlier_median: float = 3.0,
    ):
        # Determines if the data contains one distinct peak or only noise
        x_filtered = self.reject_outliers(x, outlier_median)
        self.filtered_std = np.std(x_filtered)
        peaks, properties = signal.find_peaks(
            x, prominence=self.filtered_std * prom_coef, width=wid_coef
        )
        self.prominence = (
            properties["prominences"][0] if len(properties["prominences"]) == 1 else 0
        )
        self.hasPeak = peaks.size > 0
        self.hasPeak = True
        return self.hasPeak

    def plotter(self, ax):
        self.magnitudes[self.data_var].plot(
            ax=ax, x=self.frequency_coords
        )  # Here, `self.frequency_coords` is the coordinate name
        ax.scatter(self.qubit_freq, self.spec_ampl, s=52, c="red")


class QubitSpectroscopy12MultidimAnalysis(QubitSpectroscopyMultidimAnalysis):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def analyse_qubit(self):
        self._analyse_spectroscopy()
        analysis_successful = True
        analysis_result = {
            "clock_freqs:f12": {
                "value": self.qubit_freq,
                "error": 0,
            },
            "spec:spec_ampl_12_optimal": {
                "value": self.spec_ampl,
                "error": 0,
            },
        }
        qoi = QOI(analysis_result, analysis_successful)
        return qoi


class QubitSpectroscopyNodeAnalysis(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = QubitSpectroscopyAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)


class QubitSpectroscopy12NodeMultidim(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = QubitSpectroscopy12MultidimAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)


class QubitSpectroscopyNodeMultidim(BaseAllQubitsAnalysis):
    single_qubit_analysis_obj = QubitSpectroscopyMultidimAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
