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

from tergite_autocalibration.utils.misc.helpers import generate_n_qubit_list


def test_generate_n_qubit_list_default_start():
    """Test the default starting value of 1."""
    assert generate_n_qubit_list(5) == ["q01", "q02", "q03", "q04", "q05"]


def test_generate_n_qubit_list_custom_start():
    """Test with a custom starting value."""
    assert generate_n_qubit_list(5, 10) == ["q10", "q11", "q12", "q13", "q14"]


def test_generate_n_qubit_list_single_qubit():
    """Test with a single qubit."""
    assert generate_n_qubit_list(1) == ["q01"]


def test_generate_n_qubit_list_zero_qubits():
    """Test when the number of qubits is zero."""
    assert generate_n_qubit_list(0) == []
