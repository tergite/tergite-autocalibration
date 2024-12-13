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
import xarray
from numpy import exp, pi

from tergite_autocalibration.lib.base.classification_functions import assign_state


def test_assign_state():
    qubit = "q06"
    iq_points = np.array(
        [
            2,
            2 * exp(-1j * pi / 4),
            2 * exp(1j * pi / 4),
            2 * exp(1j * 3 * pi / 4),
            2 * exp(-1j * 3 * pi / 4),
        ]
    )
    assert assign_state(qubit, iq_points) == xarray.DataArray([0, 1, 0, 2, 1])
