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

from tergite_autocalibration.lib.utils.analysis_models import AvoidedCrossings


def test_qubit_avoided_crossings():
    qubit_currents = np.array(
        [-1.60e-03, -1.52e-03, -1.44e-03, -1.36e-03, -1.28e-03, -1.20e-03, -5.60e-04]
        + [-4.80e-04, -4.00e-04, -3.20e-04, -2.40e-04, -1.60e-04, -8.00e-05, 0.00e00]
        + [8.00e-05, 1.60e-04, 2.40e-04, 3.20e-04, 4.00e-04, 4.80e-04, 5.60e-04]
        + [6.40e-04, 7.20e-04, 8.00e-04, 8.80e-04, 9.60e-04, 1.04e-03, 1.12e-03]
        + [1.20e-03, 1.28e-03, 1.84e-03, 1.92e-03]
    )

    qubit_frequencies = np.array(
        [
            5.27734444e09,
            5.27718889e09,
            5.27703333e09,
            5.27703333e09,
            5.27711111e09,
            5.27718889e09,
            5.27283333e09,
            5.27423333e09,
            5.27477778e09,
            5.27508889e09,
            5.27532222e09,
            5.27547778e09,
            5.27555556e09,
            5.27563333e09,
            5.27563333e09,
            5.27563333e09,
            5.27571111e09,
            5.27571111e09,
            5.27571111e09,
            5.27571111e09,
            5.27563333e09,
            5.27563333e09,
            5.27555556e09,
            5.27547778e09,
            5.27540000e09,
            5.27524444e09,
            5.27493333e09,
            5.27454444e09,
            5.27368889e09,
            5.27135556e09,
            5.27726667e09,
            5.27711111e09,
        ]
    )

    crossings = AvoidedCrossings(qubit_currents, qubit_frequencies, threshold=2e6)

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
<xarray.DataArray 'currents' (obs: 50)> Size: 400B
array([-2.00e-03, -1.92e-03, -1.84e-03, -1.76e-03, -1.68e-03, -1.60e-03,
       -1.52e-03, -1.44e-03, -1.36e-03, -1.28e-03, -1.20e-03, -1.12e-03,
       -1.04e-03, -9.60e-04, -8.80e-04, -8.00e-04, -7.20e-04, -6.40e-04,
       -5.60e-04, -4.80e-04, -4.00e-04, -3.20e-04, -2.40e-04, -1.60e-04,
       -8.00e-05,  0.00e+00,  8.00e-05,  1.60e-04,  2.40e-04,  3.20e-04,
        4.00e-04,  4.80e-04,  5.60e-04,  6.40e-04,  7.20e-04,  8.00e-04,
        8.80e-04,  9.60e-04,  1.04e-03,  1.12e-03,  1.20e-03,  1.28e-03,
        1.36e-03,  1.44e-03,  1.52e-03,  1.60e-03,  1.68e-03,  1.76e-03,
        1.84e-03,  1.92e-03])
Coordinates:
  * obs      (obs) object 400B MultiIndex
  * role     (obs) <U6 1kB 'target' 'target' 'target' ... 'target' 'target'
  * mode     (obs) <U5 1kB 'qubit' 'qubit' 'qubit' ... 'qubit' 'qubit' 'qubit'
ipdb> self.frequencies
<xarray.DataArray 'frequencies' (obs: 50)> Size: 400B
array([6.63187235e+09, 6.63187110e+09, 6.63187169e+09, 6.63187121e+09,
       6.63187188e+09, 6.63187099e+09, 6.63187090e+09, 6.63186602e+09,
       6.63186698e+09, 6.63187106e+09, 6.63187134e+09, 6.63187074e+09,
       6.63187184e+09, 6.63187240e+09, 6.63187234e+09, 6.63187301e+09,
       6.63187190e+09, 6.63187280e+09, 6.63187343e+09, 6.63187424e+09,
       6.63187497e+09, 6.63187746e+09, 6.63188150e+09, 6.63188758e+09,
       6.63190523e+09, 6.63201203e+09, 6.63179745e+09, 6.63183618e+09,
       6.63184485e+09, 6.63184695e+09, 6.63184637e+09, 6.63184218e+09,
       6.63182617e+09, 6.63178784e+09, 6.63193252e+09, 6.63189288e+09,
       6.63188213e+09, 6.63187807e+09, 6.63187592e+09, 6.63187471e+09,
       6.63187420e+09, 6.63187239e+09, 6.63187172e+09, 6.63187194e+09,
       6.63187199e+09, 6.63187208e+09, 6.63187150e+09, 6.63187123e+09,
       6.63187122e+09, 6.63187165e+09])
