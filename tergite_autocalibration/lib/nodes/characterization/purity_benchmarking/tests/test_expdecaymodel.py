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

import unittest
import numpy as np
from tergite_autocalibration.lib.nodes.characterization.purity_benchmarking.analysis import ExpDecayModel

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
