# This code is part of Tergite
#
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# FIXME: When it is decided which analysis we use, please put everything into the analysis.py file

import glob
from pathlib import Path
from typing import Type

import xarray as xr

from tergite_autocalibration.lib.base.analysis import BaseAnalysis
from tergite_autocalibration.lib.nodes.coupler.cz_chevron.utils.cz_FitResultStatus import (
    FitResultStatus,
)
from tergite_autocalibration.lib.nodes.coupler.cz_chevron.utils.cz_firstStepCombination import (
    CZFirstStepCombination,
    CZSimpleFitAnalysisResult,
)
from tergite_autocalibration.lib.nodes.coupler.cz_chevron.utils.cz_singleGateSimpleFit import (
    CZSingleGateSimpleFit,
)


class CZFirstStepAnalysis(BaseAnalysis):
    def __init__(
        self, baseFolder: Type[Path], date, dataFolder: Type[Path], qubit1, qubit2
    ):
        self.baseFolder = baseFolder
        self.date = date
        self.dataFolder = dataFolder
        self.q1 = qubit1
        self.q2 = qubit2
        self.freq = []

    def AnalyseGridPoint(self, folder) -> CZSimpleFitAnalysisResult:
        dataset_path = f"{self.baseFolder}/{self.dataFolder}/{folder}/dataset.hdf5"
        # print(dataset_path)
        ds = xr.open_dataset(dataset_path)
        ds_complex = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)
        d1 = ds_complex[f"yq{self.q1}"]
        d2 = ds_complex[f"yq{self.q2}"]
        d1.attrs["qubit"] = f"q{self.q1}"
        d2.attrs["qubit"] = f"q{self.q2}"
        d1 = d1.to_dataset(name=f"yq{self.q1}")
        d2 = d2.to_dataset(name=f"yq{self.q2}")
        self.freq = ds[f"cz_pulse_frequenciesq{self.q1}_q{self.q2}"].values / 1e6  # MHz
        self.times = ds[f"cz_pulse_durationsq{self.q1}_q{self.q2}"].values * 1e9  # ns
        g1 = CZSingleGateSimpleFit(d1, self.freq, self.times)
        g2 = CZSingleGateSimpleFit(d2, self.freq, self.times)
        r1 = g1.analyse_qubit()
        r2 = g2.analyse_qubit()
        # print("here")
        comb = CZFirstStepCombination(r1, r2, self.freq)
        return comb.Analyze()

    def analyse_qubit(self) -> list[float, float, float, float, float]:
        prefix = "q" + str(self.q1) + "_q" + str(self.q2) + "_" + self.date
        suffix = "all_results.py"

        # Use glob to find the file
        file_pattern = f"{self.baseFolder}/{prefix}*{suffix}"
        files = glob.glob(file_pattern)

        # Check if you found exactly one file
        if len(files) == 1:
            file_path = files[0]
            print(f"Found file: {file_path}")

            # Open and read the file
            with open(file_path, "r") as file:
                file_content = file.read()

            # Execute the file content
            local_namespace = {}
            exec(file_content, local_namespace)

            # Retrieve the dictionary
            all_results = local_namespace["all_results"]

            current_pv = 0
            bestPoint = CZSimpleFitAnalysisResult()
            best_current = 0
            best_amplitude = 0
            best_folderName = ""
            # Loop through each folder
            for element in all_results:
                folder = element["name"]
                print(folder)

                r = self.AnalyseGridPoint(folder)
                if r.status == FitResultStatus.FOUND:
                    r.Print()
                    if (
                        r.pvalue_1 + r.pvalue_2 > current_pv
                        and r.fittedParam_1[0] > 0.21
                        and r.fittedParam_2[0] > 0.21
                    ):
                        current_pv = r.pvalue_1 + r.pvalue_2
                        bestPoint = r
                        best_current = element["parking_current"]
                        best_amplitude = element["amp"]
                        best_folderName = folder

            print(best_folderName)
            print(current_pv)
            print(best_current)
            print(best_amplitude)
            print(self.freq[bestPoint.indexBestFrequency])
            print(bestPoint.fittedParam_1[1])
            print(bestPoint.fittedParam_2[1])
            return (
                best_current,
                best_amplitude,
                self.freq[bestPoint.indexBestFrequency],
                (bestPoint.fittedParam_1[1] + bestPoint.fittedParam_2[1]) / 2,
            )

        elif len(files) > 1:
            print("Error: More than one file matched the pattern.")
        else:
            print("Error: No file matched the pattern.")
            print(file_pattern)

        return None

    def plotter(self):
        print("Plot best curves")
