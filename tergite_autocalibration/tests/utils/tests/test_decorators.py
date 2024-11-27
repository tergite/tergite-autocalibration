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

import os

import pytest

from tergite_autocalibration.tests.utils.decorators import with_os_env


def test_with_os_env_sets_variables():
    """
    Test that the decorator sets the environment variables during the function call.
    """

    @with_os_env({"TEST_VAR1": "value1", "TEST_VAR2": "value2"})
    def sample_function():
        assert os.getenv("TEST_VAR1") == "value1"
        assert os.getenv("TEST_VAR2") == "value2"

    # Ensure variables are not set before the function is called
    assert os.getenv("TEST_VAR1") is None
    assert os.getenv("TEST_VAR2") is None

    # Call the decorated function
    sample_function()

    # Ensure variables are not set after the function has run
    assert os.getenv("TEST_VAR1") is None
    assert os.getenv("TEST_VAR2") is None


def test_with_os_env_restores_original_values():
    """
    Test that the decorator restores original environment variables after the function call.
    """
    os.environ["TEST_VAR1"] = "original_value1"

    @with_os_env({"TEST_VAR1": "new_value1", "TEST_VAR2": "new_value2"})
    def sample_function():
        assert os.getenv("TEST_VAR1") == "new_value1"
        assert os.getenv("TEST_VAR2") == "new_value2"

    # Ensure the original value exists before the function is called
    assert os.getenv("TEST_VAR1") == "original_value1"
    assert os.getenv("TEST_VAR2") is None

    # Call the decorated function
    sample_function()

    # Ensure original values are restored after the function call
    assert os.getenv("TEST_VAR1") == "original_value1"
    assert os.getenv("TEST_VAR2") is None


def test_with_os_env_preserves_exceptions():
    """
    Test that the decorator restores environment variables even if an exception occurs.
    """
    os.environ["TEST_VAR"] = "original_value"

    @with_os_env({"TEST_VAR": "temporary_value"})
    def sample_function():
        assert os.getenv("TEST_VAR") == "temporary_value"
        raise RuntimeError("Intentional exception")

    # Ensure the original value exists before the function is called
    assert os.getenv("TEST_VAR") == "original_value"

    # Call the decorated function and catch the exception
    with pytest.raises(RuntimeError, match="Intentional exception"):
        sample_function()

    # Ensure the original value is restored after the exception
    assert os.getenv("TEST_VAR") == "original_value"
