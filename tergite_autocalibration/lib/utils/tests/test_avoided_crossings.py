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

from tergite_autocalibration.lib.utils.analysis_models import (
    AvoidedCrossings,
    ResonatorAvoidedCrossings,
)


def test_qubit_avoided_crossings():
    currents = np.array(
        [-1.60e-03, -1.52e-03, -1.44e-03, -1.36e-03, -1.28e-03, -1.20e-03, -5.60e-04]
        + [-4.80e-04, -4.00e-04, -3.20e-04, -2.40e-04, -1.60e-04, -8.00e-05, 0.00e00]
        + [8.00e-05, 1.60e-04, 2.40e-04, 3.20e-04, 4.00e-04, 4.80e-04, 5.60e-04]
        + [6.40e-04, 7.20e-04, 8.00e-04, 8.80e-04, 9.60e-04, 1.04e-03, 1.12e-03]
        + [1.20e-03, 1.28e-03, 1.84e-03, 1.92e-03]
    )

    qubit_frequencies = np.array(
        [5.27734444e09, 5.27718889e09, 5.27703333e09, 5.27703333e09, 5.27711111e09]
        + [5.27718889e09, 5.27283333e09, 5.27423333e09, 5.27477778e09, 5.27508889e09]
        + [5.27532222e09, 5.27547778e09, 5.27555556e09, 5.27563333e09, 5.27563333e09]
        + [5.27563333e09, 5.27571111e09, 5.27571111e09, 5.27571111e09, 5.27571111e09]
        + [5.27563333e09, 5.27563333e09, 5.27555556e09, 5.27547778e09, 5.27540000e09]
        + [5.27524444e09, 5.27493333e09, 5.27454444e09, 5.27368889e09, 5.27135556e09]
        + [5.27726667e09, 5.27711111e09]
    )

    crossings = AvoidedCrossings(currents, qubit_frequencies, threshold=2e6)

    cross_currents = crossings.crossing_currents
    assert len(cross_currents) == 2
    assert pytest.approx(cross_currents[0]) == -0.00088
    assert pytest.approx(cross_currents[1]) == 0.00156

    cross_frequency = crossings.crossing_frequency.value
    cross_freq_above = crossings.crossing_frequency.above
    cross_freq_below = crossings.crossing_frequency.below

    assert pytest.approx(cross_frequency) == 5276372220.0
    assert pytest.approx(cross_freq_above) == 5277033330.0
    assert pytest.approx(cross_freq_below) == 5275711110.0

    assert crossings.I0_hint is None
    assert pytest.approx(crossings.Ic_hint) == 0.00036


def test_parity_of_jump():
    frequencies = np.array([5.0, 5.2, 3.0, 3.2])
    jump = 1

    parity = AvoidedCrossings._parity_of_jump(jump, frequencies)
    assert parity == (+1, -1, +1)

    frequencies = np.array([5.4, 5.0, 4.8, 7.0, 6.8])
    jump = 2

    parity = AvoidedCrossings._parity_of_jump(jump, frequencies)
    assert parity == (-1, +1, -1)


def test_resonator_avoided_crossings():
    currents = np.array(
        [-2.00e-03, -1.92e-03, -1.84e-03, -1.76e-03, -1.68e-03, -1.60e-03, -1.52e-03]
        + [-1.44e-03, -1.36e-03, -1.28e-03, -1.20e-03, -1.12e-03, -1.04e-03, -9.60e-04]
        + [-8.80e-04, -8.00e-04, -7.20e-04, -6.40e-04, -5.60e-04, -4.80e-04, -4.00e-04]
        + [-3.20e-04, -2.40e-04, -1.60e-04, -8.00e-05, 0.00e00, 8.00e-05, 1.60e-04]
        + [2.40e-04, 3.20e-04, 4.00e-04, 4.80e-04, 5.60e-04, 6.40e-04, 7.20e-04]
        + [8.00e-04, 8.80e-04, 9.60e-04, 1.04e-03, 1.12e-03, 1.20e-03, 1.28e-03]
        + [1.36e-03, 1.44e-03, 1.52e-03, 1.60e-03, 1.68e-03, 1.76e-03]
        + [1.84e-03, 1.92e-03]
    )
    ro_frequencies = np.array(
        [7.18133403e09, 7.18133352e09, 7.18133207e09, 7.18133376e09, 7.18133303e09]
        + [7.18133285e09, 7.18133302e09, 7.18133306e09, 7.18133235e09, 7.18133292e09]
        + [7.18133179e09, 7.18133263e09, 7.18133356e09, 7.18133380e09, 7.18133322e09]
        + [7.18133395e09, 7.18133333e09, 7.18133519e09, 7.18133459e09, 7.18133492e09]
        + [7.18133559e09, 7.18133490e09, 7.18133645e09, 7.18133638e09, 7.18133512e09]
        + [7.18133726e09, 7.18133628e09, 7.18133671e09, 7.18133721e09, 7.18133662e09]
        + [7.18133709e09, 7.18133848e09, 7.18133769e09, 7.18133828e09, 7.18133769e09]
        + [7.18133668e09, 7.18133693e09, 7.18133795e09, 7.18133619e09, 7.18133554e09]
        + [7.18133632e09, 7.18133454e09, 7.18133589e09, 7.18133548e09, 7.18133346e09]
        + [7.18133380e09, 7.18133416e09, 7.18133396e09, 7.18133331e09, 7.18133411e09]
    )

    crossings = ResonatorAvoidedCrossings(currents, ro_frequencies)
    breakpoint()
    cross_currents = crossings.crossing_currents
    # assert len(cross_currents) == 2
    # assert pytest.approx(cross_currents[0]) == -0.00088
    # assert pytest.approx(cross_currents[1]) == 0.00156

    cross_frequency = crossings.crossing_frequency

    # assert pytest.approx(cross_frequency) == 5276372220.0

    # assert crossings.I0_hint is None
