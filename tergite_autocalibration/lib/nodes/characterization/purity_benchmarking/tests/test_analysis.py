import unittest
import numpy as np
import xarray as xr
from lmfit.model import ModelResult
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
    def setUpClass(cls):
        # Load or create the dataset
        cls.dataset = xr.Dataset({"purity": (["cliffords", "seed"], np.random.rand(20, 5))}, 
                                 coords={"cliffords": np.arange(20), "seed": np.arange(5)})
        cls.dataset["purity"].attrs["qubit"] = "q1"

    def test_initialization(self):
        analysis = PurityBenchmarkingAnalysis(self.dataset)
        self.assertEqual(analysis.qubit, self.dataset['purity'].attrs['qubit'])
        self.assertEqual(analysis.number_of_repetitions, self.dataset.sizes['seed'])
        self.assertEqual(len(analysis.number_of_cliffords), len(self.dataset['cliffords']) - 3)
        

    def test_run_fitting(self):
        # Initialize the analysis
        analysis = PurityBenchmarkingAnalysis(self.dataset)
        # Process the data
        fidelity = analysis._process_and_normalize_data()
        # Ensure that the purity data is correctly calculated
        self.assertTrue(analysis.purity_results_dict)
        # Run the fitting procedure
        self.assertIsInstance(fidelity, list)
        self.assertTrue(len(fidelity) > 0)
        self.assertTrue(0 <= fidelity[0] <= 1)
        self.assertIsInstance(analysis.fit_results, ModelResult)

    def test_plotter(self):
        analysis = PurityBenchmarkingAnalysis(self.dataset)
        analysis.run_fitting()

        fig = Figure()
        ax = fig.subplots()
        analysis.plotter(ax)
        self.assertEqual(len(ax.lines), 2)  # Check that two lines were plotted (data and fit)

if __name__ == '__main__':
    unittest.main()
