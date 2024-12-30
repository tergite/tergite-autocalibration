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

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.lib.utils.classification_functions import assign_state


def test_assign_state():
    qubit = "q06"
    # centroid_I = 1
    # centroid_Q = 0
    # omega_01 = 330
    # omega_12 = 180
    # omega_20 = 90
    REDIS_CONNECTION.hset(f"transmons:{qubit}", "centroid_I", "1")
    REDIS_CONNECTION.hset(f"transmons:{qubit}", "centroid_Q", "0")
    REDIS_CONNECTION.hset(f"transmons:{qubit}", "omega_01", "330")
    REDIS_CONNECTION.hset(f"transmons:{qubit}", "omega_12", "180")
    REDIS_CONNECTION.hset(f"transmons:{qubit}", "omega_20", "90")

    iq_points = np.array(
        [
            2,
            2 * exp(-1j * pi / 4),
            2 * exp(1j * pi / 4),
            2 * exp(1j * 3 * pi / 4),
            2 * exp(-1j * 3 * pi / 4),
        ]
    )
    assert xarray.DataArray([0, 1, 0, 2, 1]).equals(
        xarray.DataArray(assign_state(qubit, iq_points))
    )
