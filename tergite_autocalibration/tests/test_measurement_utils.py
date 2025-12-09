# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2025
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

from tergite_autocalibration.utils.measurement_utils import (
    reduce_samplespace,
    samplespace_dimensions,
)

# Small samplespace for easy tests
_simple_samplespace = {
    "frequencies": {
        "q1": np.array([4.0e9, 4.1e9, 4.2e9]),
        "q2": np.array([4.5e9, 4.6e9, 4.7e9]),
    }
}

# Samplespace to be used for the samplespace dimensions tests
_samplespace = {
    "frequencies": {
        "q1": np.array([4.0e9, 4.1e9, 4.2e9]),
        "q2": np.array([4.5e9, 4.6e9, 4.7e9]),
    },
    "amplitudes": {
        "q1": np.array([0.1, 0.2, 0.3, 0.4, 0.5]),
        "q2": np.array([0.2, 0.3, 0.4, 0.5, 0.6]),
    },
}


def test_reduce_samplespace_base_case():
    """
    Base case with one-dimensional samplespace
    """
    reduced_external_samplespace_result = reduce_samplespace(2, _simple_samplespace)
    reduced_external_samplespace = {
        "frequencies": {
            "q1": np.array([4.2e9]),
            "q2": np.array([4.7e9]),
        }
    }
    assert reduced_external_samplespace == reduced_external_samplespace_result


def test_reduce_samplespace_two_dimensions():
    """
    Test whether the function can handle two-dimensional samplespaces.
    The second dimensions will be ignored.
    """
    reduced_external_samplespace_result = reduce_samplespace(2, _samplespace)
    reduced_external_samplespace = {
        "frequencies": {
            "q1": np.array([4.2e9]),
            "q2": np.array([4.7e9]),
        }
    }
    assert reduced_external_samplespace == reduced_external_samplespace_result


def test_reduce_samplespace_index_out_of_bounds():
    """
    Test what happens when the index goes ouf ot range
    """
    with pytest.raises(IndexError):
        reduce_samplespace(4, _simple_samplespace)


def test_reduce_samplespace_empty():
    """
    Test with empty samplespace
    """
    assert reduce_samplespace(0, {}) == {}
    assert reduce_samplespace(1, {}) == {}


def test_samplespace_dimensions_base_case():
    """
    Base case with two-dimensional samplespace
    """
    dimensions = samplespace_dimensions(_samplespace)
    assert dimensions == [3, 5]


def test_samplespace_dimensions_with_loops():
    """
    Base case with two-dimensional samplespace and loops
    """
    dimensions = samplespace_dimensions(_samplespace, 4)
    assert dimensions == [3, 5, 4]


def test_samplespace_dimensions_empty():
    """
    Test with empty samplespace
    """
    dimensions = samplespace_dimensions({})
    assert dimensions == []
