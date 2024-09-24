# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Michele Faucci Giannelli 2024
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
import xarray as xr
from numpy.polynomial.polynomial import Polynomial

from ...qubit_control.spectroscopy.analysis import (
    QubitSpectroscopyMultidim,
    QubitSpectroscopyNodeAnalysis,
    QubitSpectroscopyNodeMultidim,
)
from ....base.analysis import BaseAllCouplersAnalysis, BaseAnalysis


class CouplerSpectroscopyQubitAnalysis(QubitSpectroscopyMultidim):
    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)

    def reject_outliers(self, data, m=4):
        d = np.abs(data - np.median(data))
        mdev = np.median(d)
        s = d / mdev if mdev else np.zeros(len(d))
        return np.array(s > m)

    def analyse_qubit(self):
        for coord in self.dataset[self.data_var].coords:
            if "frequencies" in coord:
                self.frequencies = coord
            elif "currents" in coord:
                self.currents = coord
        #self.dataset = self.dataset.sortby(self.currents)

        self.dc_currents = self.dataset[f"y{self.qubit}"][self.currents]
        self.detected_frequencies = []
        self.detected_currents = []
        for i, current in enumerate(self.dc_currents.values):
            qubit_frequency = super()._analyze_qubit()
            if not np.isnan(qubit_frequency):
                self.detected_frequencies.append(qubit_frequency)
                self.detected_currents.append(current)

        distances = np.abs(np.gradient(self.detected_frequencies))
        # the reject_outliers array has True at gradient discontinuities
        array_splits = self.reject_outliers(distances).nonzero()[0] + 1
        frequency_splits = np.split(self.detected_frequencies, array_splits)
        currents_splits = np.split(self.detected_currents, array_splits)
        split_data = zip(currents_splits, frequency_splits)
        roots = []
        root_frequencies = []
        for split_currents, split_frequencies in split_data:
            if len(split_frequencies) > 4:
                coupler_fit = Polynomial.fit(split_currents, split_frequencies, 4)
                # fit_currents = np.linspace(split_currents[0], split_currents[-1], 100)
                root = np.mean(np.real(coupler_fit.roots()))
                roots.append(root)
                root_frequencies.append(coupler_fit(root))
        if len(roots) == 0:
            print("No Roots Found, returning zero current")
            return [0]
        I0 = roots[np.argmin(np.abs(roots))]
        I1 = roots[np.argmax(np.abs(roots))]
        DeltaI = I1 - I0
        possible_I = np.array([0.4 * DeltaI + I0, 0.4 * DeltaI - I0])
        self.parking_I = possible_I[np.argmin(np.abs(possible_I))]
        self.roots = roots
        self.root_frequencies = root_frequencies
        return [self.parking_I, DeltaI]

    def plotter(self, ax: plt.Axes):
        self.dataset[self.data_var].plot(ax=ax, x=self.frequencies)
        ax.scatter(self.detected_frequencies, self.detected_currents, s=52, c="red")
        if hasattr(self, "root_frequencies"):
            ax.scatter(
                self.root_frequencies, self.roots, s=64, c="black", label=r"$\Phi_0$"
            )
        if hasattr(self, "parking_I"):
            ax.axhline(
                self.parking_I,
                lw=5,
                ls="dashed",
                c="orange",
                label=f"parking current = {self.parking_I}",
            )

class CouplerSpectroscopyNodeAnalysis(BaseAllCouplersAnalysis):
    single_qubit_analysis_obj = CouplerSpectroscopyQubitAnalysis

    def __init__(self, name, redis_fields):
        super().__init__(name, redis_fields)
        self.repeat_coordinate_name = "repeat"