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

from tergite_autocalibration.utils.regex import camel_to_snake


def test_basic_conversion():
    assert camel_to_snake("CamelCaseString") == "camel_case_string"
    assert camel_to_snake("SimpleTest") == "simple_test"


def test_acronym_handling():
    assert camel_to_snake("HTTPServerError") == "http_server_error"


def test_number_handling():
    assert camel_to_snake("Camel1CaseString") == "camel_1_case_string"
    assert camel_to_snake("Version1Point0") == "version_1_point_0"


def test_single_letter_cases():
    assert camel_to_snake("A") == "a"
    assert camel_to_snake("ABC") == "abc"
    assert camel_to_snake("AB") == "ab"
    assert camel_to_snake("Ab") == "ab"
    assert camel_to_snake("aB") == "a_b"


def test_mixed_case_with_numbers_and_acronyms():
    assert (
        camel_to_snake("ROAmplitude2StateOptimization")
        == "ro_amplitude_2_state_optimization"
    )


def test_empty_string():
    assert camel_to_snake("") == ""


def test_already_snake_case():
    assert camel_to_snake("already_snake_case") == "already_snake_case"
    assert camel_to_snake("Capital_But_Snake") == "capital_but_snake"
