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

from pathlib import Path
import unittest

from lmfit.model import ModelResult
from matplotlib.figure import Figure
import numpy as np
import xarray as xr

from tergite_autocalibration.lib.nodes.characterization.purity_benchmarking.analysis import (
    PurityBenchmarkingQubitAnalysis,
)
from tergite_autocalibration.tests.utils.env import setup_test_env

setup_test_env()




# FIXME: These tests are marked as skip after the refactoring of the analysis classes
#        Michele to integrate with new data files from Joel
class TestPurityBenchmarkingAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Setup the dataset for testing from a file
        test_dir = Path(__file__).parent
        file_path = test_dir / "data" / "dataset_0.hdf5"  # "testdata.hdf5"
        self.dataset = xr.open_dataset(file_path)

    @unittest.skip
    def test_initialization(self):
        self.analysis = PurityBenchmarkingQubitAnalysis("name", ["purity_fidelity"])
        self.analysis.process_qubit(self.dataset, "yq06")
        # Check that the analysis object has the expected attributes
        self.assertTrue(hasattr(self.analysis, "purity_results_dict"))
        self.assertTrue(hasattr(self.analysis, "normalized_data_dict"))
        self.assertEqual(
            self.analysis.number_of_repetitions, self.dataset.sizes.get("seed", 1)
        )

    @unittest.skip
    def test_run_fitting(self):
        analysis = PurityBenchmarkingQubitAnalysis("name", ["redis_field"])
        analysis.process_qubit(self.dataset, "yq06")
        # Verify the average purity result is within the expected range
        self.assertTrue(
            0.7 < np.average(list(analysis.purity_results_dict.values())) < 0.8
        )

        # Trim the dataset to only 5 Cliffords before running the fitting so it will fit the model
        analysis.number_of_cliffords = analysis.number_of_cliffords[:5]
        for key in analysis.purity_results_dict.keys():
            analysis.purity_results_dict[key] = analysis.purity_results_dict[key][:5]
        fidelity = analysis.analyse_qubit()

        # Verify that the fitting results are valid
        self.assertIsInstance(fidelity, list)
        self.assertTrue(len(fidelity) > 0.99)
        self.assertTrue(0 <= fidelity[0] <= 1.002)
        self.assertIsInstance(analysis.fit_results, ModelResult)

    @unittest.skip
    def test_plotter(self):
        analysis = PurityBenchmarkingQubitAnalysis("name", ["redis_field"])
        analysis.process_qubit(self.dataset, "yq14")

        # Trim the dataset to only 5 Cliffords before plotting, same reason as above
        analysis.number_of_cliffords = analysis.number_of_cliffords[:5]
        for key in analysis.purity_results_dict.keys():
            analysis.purity_results_dict[key] = analysis.purity_results_dict[key][:5]

        analysis.analyse_qubit()
        fig = Figure()
        ax = fig.subplots()
        analysis.plotter(ax)

        # Check that three lines were plotted (data and fit)
        self.assertEqual(len(ax.lines), 3)


if __name__ == "__main__":
    unittest.main()
