# This code is part of Tergite
#
# (C) Copyright Joel Sandås 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from tergite_autocalibration.tests.utils.env import setup_test_env

setup_test_env()

from tergite_autocalibration.tests.utils.env import setup_test_env

setup_test_env()

import unittest
import numpy as np
import xarray as xr
from lmfit.model import ModelResult
from pathlib import Path
from matplotlib.figure import Figure
from tergite_autocalibration.lib.nodes.characterization.purity_benchmarking.analysis import (
    PurityBenchmarkingAnalysis,
)


class TestPurityBenchmarkingAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Setup the dataset for testing from a file
        test_dir = Path(__file__).parent
        file_path = test_dir / "testdata.hdf5"
        self.dataset = xr.open_dataset(file_path)

    def test_initialization(self):
        self.analysis = PurityBenchmarkingAnalysis(self.dataset)
        # Check that the analysis object has the expected attributes
        self.assertTrue(hasattr(self.analysis, "purity"))
        self.assertTrue(hasattr(self.analysis, "normalized_data_dict"))
        self.assertEqual(
            self.analysis.number_of_repetitions, self.dataset.sizes.get("seed", 1)
        )

    def test_run_fitting(self):
        analysis = PurityBenchmarkingAnalysis(self.dataset)
        # Verify the average purity result is within the expected range
        print(
            (
                np.sum(list(analysis.purity_results_dict.values()))
                / len(analysis.purity_results_dict)
            )
        )
        self.assertTrue(
            56.1
            <= (
                np.sum(list(analysis.purity_results_dict.values()))
                / len(analysis.purity_results_dict)
            )
            <= 56.2
        )

        # Trim the dataset to only 5 Cliffords before running the fitting so it will fit the model
        analysis.number_of_cliffords = analysis.number_of_cliffords[:5]
        for key in analysis.purity_results_dict.keys():
            analysis.purity_results_dict[key] = analysis.purity_results_dict[key][:5]
        fidelity = analysis.run_fitting()

        # Verify that the fitting results are valid
        self.assertIsInstance(fidelity, list)
        self.assertTrue(len(fidelity) > 0)
        self.assertTrue(0 <= fidelity[0] <= 1.002)
        self.assertIsInstance(analysis.fit_results, ModelResult)

    def test_plotter(self):
        analysis = PurityBenchmarkingAnalysis(self.dataset)

        # Trim the dataset to only 5 Cliffords before plotting, same reason as above
        analysis.number_of_cliffords = analysis.number_of_cliffords[:5]
        for key in analysis.purity_results_dict.keys():
            analysis.purity_results_dict[key] = analysis.purity_results_dict[key][:5]

        analysis.run_fitting()
        fig = Figure()
        ax = fig.subplots()
        analysis.plotter(ax)

        # Check that three lines were plotted (data and fit)
        self.assertEqual(len(ax.lines), 3)


if __name__ == "__main__":
    unittest.main()