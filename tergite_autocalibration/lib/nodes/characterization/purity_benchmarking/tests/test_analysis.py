import unittest
import numpy as np
import xarray as xr
from lmfit.model import ModelResult
from pathlib import Path
from matplotlib.figure import Figure
from tergite_autocalibration.lib.nodes.characterization.purity_benchmarking.analysis import ExpDecayModel, PurityBenchmarkingAnalysis

class TestExpDecayModel(unittest.TestCase):
    def test_exponential_decay_model_initialization(self):
        model = ExpDecayModel()
        # Ensure the model has parameter hints for 'A', 'B', and 'p'
        self.assertTrue('A' in model.param_hints)
        self.assertTrue('B' in model.param_hints)
        self.assertTrue('p' in model.param_hints)
        # Verify that 'B' and 'p' have a minimum value of 0
        self.assertEqual(model.param_hints['B']['min'], 0)
        self.assertEqual(model.param_hints['p']['min'], 0)

    def test_guess_parameters(self):
        model = ExpDecayModel()
        data = np.array([1.0, 0.8, 0.6, 0.4, 0.2])  # Example data
        m = np.array([0, 1, 2, 3, 4])  # Example m values
        params = model.guess(data, m=m)
        # Verify that the guessed parameters are close to expected values
        self.assertAlmostEqual(params['A'].value, 1.0)
        self.assertAlmostEqual(params['B'].value, 0.8)
        self.assertAlmostEqual(params['p'].value, 0.95)

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
        self.assertEqual(self.analysis.number_of_repetitions, self.dataset.sizes.get("seed", 1))        

    def test_run_fitting(self):
        analysis = PurityBenchmarkingAnalysis(self.dataset)
        analysis._process_and_normalize_data()
        # Verify the average purity result is within the expected range
        print((np.sum(list(analysis.purity_results_dict.values()))/len(analysis.purity_results_dict)))
        self.assertTrue(56.1 <= (np.sum(list(analysis.purity_results_dict.values()))/len(analysis.purity_results_dict)) <= 56.2)

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
        analysis._process_and_normalize_data()

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

if __name__ == '__main__':
    unittest.main()
