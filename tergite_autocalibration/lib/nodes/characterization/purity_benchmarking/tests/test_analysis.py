import unittest
import numpy as np
import xarray as xr
from lmfit.model import ModelResult
from pathlib import Path
from matplotlib.figure import Figure
from tergite_autocalibration.lib.nodes.characterization.purity_benchmarking.analysis import ExpDecayModel, PurityBenchmarkingAnalysis  # Replace with actual import path

class TestExpDecayModel(unittest.TestCase):
    def test_exponential_decay_model_initialization(self):
        model = ExpDecayModel()
        self.assertTrue('A' in model.param_hints)
        self.assertTrue('B' in model.param_hints)
        self.assertTrue('p' in model.param_hints)
        self.assertEqual(model.param_hints['B']['min'], 0)
        self.assertEqual(model.param_hints['p']['min'], 0)

    def test_guess_parameters(self):
        model = ExpDecayModel()
        data = np.array([1.0, 0.8, 0.6, 0.4, 0.2])
        m = np.array([0, 1, 2, 3, 4])
        params = model.guess(data, m=m)
        self.assertAlmostEqual(params['A'].value, 1.0)
        self.assertAlmostEqual(params['B'].value, 0.2)
        self.assertAlmostEqual(params['p'].value, 0.95)

class TestPurityBenchmarkingAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        test_dir = Path(__file__).parent
        file_path = test_dir / "testdata.hdf5"
        self.dataset = xr.open_dataset(file_path)

    def test_initialization(self):
        self.analysis = PurityBenchmarkingAnalysis(self.dataset)
        self.assertTrue(hasattr(self.analysis, "purity"))
        self.assertTrue(hasattr(self.analysis, "normalized_data_dict"))
        self.assertEqual(self.analysis.number_of_repetitions, self.dataset.sizes.get("seed", 1))        

    def test_run_fitting(self):
        # Initialize the analysis
        analysis = PurityBenchmarkingAnalysis(self.dataset)
        # Process the data
        analysis._process_and_normalize_data()

        # Trim the dataset to only 5 Cliffords before running the fitting
        analysis.number_of_cliffords = analysis.number_of_cliffords[:5]
        for key in analysis.purity_results_dict.keys():
            analysis.purity_results_dict[key] = analysis.purity_results_dict[key][:5]

        # Run the fitting procedure on the trimmed data
        fidelity = analysis.run_fitting()

        self.assertIsInstance(fidelity, list)
        self.assertTrue(len(fidelity) > 0)
        print(fidelity[0])
        self.assertTrue(0 <= fidelity[0] <= 1.1)
        self.assertIsInstance(analysis.fit_results, ModelResult)

    def test_plotter(self):
        analysis = PurityBenchmarkingAnalysis(self.dataset)
        analysis._process_and_normalize_data()

        # Trim the dataset to only 5 Cliffords before plotting
        analysis.number_of_cliffords = analysis.number_of_cliffords[:5]
        for key in analysis.purity_results_dict.keys():
            analysis.purity_results_dict[key] = analysis.purity_results_dict[key][:5]

        # Run the fitting procedure on the trimmed data
        analysis.run_fitting()

        # Create a figure and axis for plotting
        fig = Figure()
        ax = fig.subplots()
        # Plot the data and fitted curve
        analysis.plotter(ax)
        
        # Check that two lines were plotted (data and fit)
        self.assertEqual(len(ax.lines), 3)

if __name__ == '__main__':
    unittest.main()
