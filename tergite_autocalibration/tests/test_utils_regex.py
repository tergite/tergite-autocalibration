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

from tergite_autocalibration.utils.misc.regex import (
    camel_to_snake,
    is_bool,
    str_to_bool,
)


def test_camel_basic_conversion():
    assert camel_to_snake("CamelCaseString") == "camel_case_string"
    assert camel_to_snake("SimpleTest") == "simple_test"


def test_camel_acronym_handling():
    assert camel_to_snake("HTTPServerError") == "http_server_error"


def test_camel_number_handling():
    assert camel_to_snake("Camel1CaseString") == "camel_1_case_string"
    assert camel_to_snake("Version1Point0") == "version_1_point_0"


def test_camel_single_letter_cases():
    assert camel_to_snake("A") == "a"
    assert camel_to_snake("ABC") == "abc"
    assert camel_to_snake("AB") == "ab"
    assert camel_to_snake("Ab") == "ab"
    assert camel_to_snake("aB") == "a_b"


def test_camel_mixed_case_with_numbers_and_acronyms():
    assert (
        camel_to_snake("ROAmplitude2StateOptimization")
        == "ro_amplitude_2_state_optimization"
    )


def test_camel_empty_string():
    assert camel_to_snake("") == ""


def test_camel_already_snake_case():
    assert camel_to_snake("already_snake_case") == "already_snake_case"
    assert camel_to_snake("Capital_But_Snake") == "capital_but_snake"


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("true", True),  # Valid boolean (lowercase)
        ("false", True),  # Valid boolean (lowercase)
        ("True", True),  # Valid boolean (uppercase first letter)
        ("False", True),  # Valid boolean (uppercase first letter)
        ("TrUe", True),  # Valid boolean (mixed case)
        ("FaLsE", True),  # Valid boolean (mixed case)
        ("yes", False),  # Invalid input
        ("no", False),  # Invalid input
        ("1", False),  # Invalid input
        ("0", False),  # Invalid input
        ("maybe", False),  # Invalid input
        ("", False),  # Empty string
        ("   ", False),  # Whitespace string
    ],
)
def test_is_bool(input_str, expected):
    assert is_bool(input_str) == expected


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("true", True),  # Valid boolean (lowercase)
        ("false", False),  # Valid boolean (lowercase)
        ("True", True),  # Valid boolean (uppercase first letter)
        ("False", False),  # Valid boolean (uppercase first letter)
        ("TrUe", True),  # Valid boolean (mixed case)
        ("FaLsE", False),  # Valid boolean (mixed case)
    ],
)
def test_str_to_bool_valid(input_str, expected):
    assert str_to_bool(input_str) == expected


@pytest.mark.parametrize(
    "input_str",
    [
        "yes",  # Invalid input
        "no",  # Invalid input
        "1",  # Invalid input
        "0",  # Invalid input
        "maybe",  # Invalid input
        "",  # Empty string
        "   ",  # Whitespace-only string
    ],
)
def test_str_to_bool_invalid(input_str):
    with pytest.raises(
        TypeError, match=f"String {input_str.strip()} cannot be casted to bool."
    ):
        str_to_bool(input_str)
