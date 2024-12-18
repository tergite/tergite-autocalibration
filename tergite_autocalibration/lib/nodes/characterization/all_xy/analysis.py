# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np
import xarray as xr

from tergite_autocalibration.lib.base.analysis import BaseAnalysis
from tergite_autocalibration.lib.nodes.characterization.all_xy.measurement import (
    all_XY_angles,
)


class AllXYAnalysis(BaseAnalysis):
    def __init__(self, dataset: xr.Dataset):
        super().__init__()
        data_var = list(dataset.data_vars.keys())[0]
        coord = list(dataset[data_var].coords.keys())[0]
        self.S21 = dataset[data_var].values
        self.independents = dataset[coord].values
        self.calibration_0 = self.S21[-2]
        self.calibration_1 = self.S21[-1]
        self.magnitudes = np.absolute(self.S21[:-2])
        self.fit_results = {}
        self.qubit = dataset[data_var].attrs["qubit"]

    def string_representation(self, operation: dict):
        if operation["phi"] == 0:
            if operation["theta"] == 0:
                str_label = "I"
            elif operation["theta"] == 90:
                str_label = "X90"
            elif operation["theta"] == 180:
                str_label = "X"
        elif operation["phi"] == 90:
            if operation["theta"] == 90:
                str_label = "Y90"
            elif operation["theta"] == 180:
                str_label = "Y"
        return str_label

    def analyse_qubit(self):
        self.rotated_data = self.rotate_to_probability_axis(self.S21)
        labels = []
        for index in self.independents[:-2]:
            operation1, operation2 = all_XY_angles[index]
            label = self.string_representation(operation1) + self.string_representation(
                operation2
            )
            labels.append(label)

        self.x_labels = labels

        return [0]

    def plotter(self, ax):
        ax.set_title(f"All-XY analysis_base for {self.qubit}")
        ax.scatter(self.independents[:-2], self.rotated_data, marker="o", s=48)
        ax.set_xlabel("Gate")
        ax.set_xticks(self.independents[:-2])
        ax.set_xticklabels(self.x_labels, rotation=90)
        ax.set_ylabel("|S21| (V)")
        ax.grid()
