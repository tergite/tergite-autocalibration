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

from ..config.parsers import (
    parse_input_qubit,
)

def test_single_space_separated():
    input_str = "q01 q02 q03"
    expected_output = ["q01", "q02", "q03"]
    assert parse_input_qubit(input_str) == expected_output


def test_single_comma_separated():
    input_str = "q01,q02,q03"
    expected_output = ["q01", "q02", "q03"]
    assert parse_input_qubit(input_str) == expected_output


def test_single_comma_and_space_separated():
    input_str = "q01, q02, q03"
    expected_output = ["q01", "q02", "q03"]
    assert parse_input_qubit(input_str) == expected_output


def test_range():
    input_str = "q01-q03"
    expected_output = ["q01", "q02", "q03"]
    assert parse_input_qubit(input_str) == expected_output


def test_mixed_spaces_and_ranges():
    input_str = "q01 q02 q03-q05"
    expected_output = ["q01", "q02", "q03", "q04", "q05"]
    assert parse_input_qubit(input_str) == expected_output


def test_multiple_ranges_and_separators():
    input_str = "q01 q03-q05, q07, q08-q10"
    expected_output = ["q01", "q03", "q04", "q05", "q07", "q08", "q09", "q10"]
    assert parse_input_qubit(input_str) == expected_output


def test_duplicate_handling():
    input_str = "q01 q02 q02 q03, q03, q03-q05"
    expected_output = ["q01", "q02", "q03", "q04", "q05"]
    assert parse_input_qubit(input_str) == expected_output


def test_non_sequential_range():
    input_str = "q05-q03"
    expected_output = ["q03", "q04", "q05"]
    assert parse_input_qubit(input_str) == expected_output


def test_non_alphanumeric_prefix():
    input_str = "p01 p02-p04"
    expected_output = ["p01", "p02", "p03", "p04"]
    assert parse_input_qubit(input_str) == expected_output


def test_empty_input():
    input_str = ""
    expected_output = []
    assert parse_input_qubit(input_str) == expected_output


def test_irregular_spacing_and_commas():
    input_str = " q01 ,   q02 , q03-q05 "
    expected_output = ["q01", "q02", "q03", "q04", "q05"]
    assert parse_input_qubit(input_str) == expected_output
