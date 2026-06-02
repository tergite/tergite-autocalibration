# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np
import pytest

from tergite_autocalibration.lib.utils.analysis_models import straighten_ramsey_points


def test_straighten_ramsey_points():

    artificial_detunings = np.array(
        [-2100000.0, -1300000.0, -500000.0, 300000.0, 1100000.0, 1900000.0]
    )

    fitter_detunings = np.array([2112069, 1308156, 493336, 289615, 1080305, 1882779])

    linear_fitted_detunings = straighten_ramsey_points(
        artificial_detunings, fitter_detunings
    )
    correct_fits = np.array([-2112069, -1308156, -493336, 289615, 1080305, 1882779])
    assert pytest.approx(linear_fitted_detunings) == correct_fits
