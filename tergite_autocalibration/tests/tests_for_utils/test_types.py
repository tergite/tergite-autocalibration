# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import pytest

from tergite_autocalibration.utils.misc.types import (
    safe_str_to_bool_int_float,
)  # Adjust the import according to your project structure


def test_safe_str_to_type_bool():
    # Test valid boolean strings
    assert safe_str_to_bool_int_float(bool, "True") is True
    assert safe_str_to_bool_int_float(bool, "true") is True
    assert safe_str_to_bool_int_float(bool, "False") is False
    assert safe_str_to_bool_int_float(bool, "false") is False

    # Test invalid boolean strings
    assert safe_str_to_bool_int_float(bool, "invalid") is False
    assert safe_str_to_bool_int_float(bool, "") is False


def test_safe_str_to_type_int():
    # Test valid integer strings
    assert safe_str_to_bool_int_float(int, "123") == 123
    assert safe_str_to_bool_int_float(int, "-456") == -456
    assert safe_str_to_bool_int_float(int, "0") == 0

    # Test invalid integer strings
    with pytest.raises(ValueError):
        safe_str_to_bool_int_float(int, "abc")
    with pytest.raises(ValueError):
        safe_str_to_bool_int_float(int, "12.34")
    with pytest.raises(ValueError):
        safe_str_to_bool_int_float(int, "")


def test_safe_str_to_type_float():
    # Test valid float strings
    assert safe_str_to_bool_int_float(float, "123.45") == 123.45
    assert safe_str_to_bool_int_float(float, "-678.90") == -678.90
    assert safe_str_to_bool_int_float(float, "0.0") == 0.0

    # Test invalid float strings
    with pytest.raises(ValueError):
        safe_str_to_bool_int_float(float, "abc")
    with pytest.raises(ValueError):
        safe_str_to_bool_int_float(float, "123,45")
    with pytest.raises(ValueError):
        safe_str_to_bool_int_float(float, "")


def test_safe_str_to_type_str():
    # Test default string behavior
    assert safe_str_to_bool_int_float(str, "hello") == "hello"
    assert safe_str_to_bool_int_float(str, "") == ""
