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

from tergite_autocalibration.tests.utils.decorators import with_os_env, preserve_os_env


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


# Sample function that we will decorate with preserve_os_env
@preserve_os_env
def sample_function_preserve_os_env():
    os.environ["TEMP_VAR"] = "temporary_value"
    return os.environ.get("TEMP_VAR")


def test_preserve_os_env():
    """
    Check that the environment variable is preserved
    """

    # Set an initial value for TEMP_VAR
    os.environ["TEMP_VAR"] = "initial_value"

    # Call the decorated function
    result = sample_function_preserve_os_env()

    # Ensure the environment variable is restored after the function call
    assert os.environ.get("TEMP_VAR") == "initial_value"
    # Ensure the function works and returns the correct result
    assert result == "temporary_value"


def test_preserve_os_env_with_exception():
    """
    Check that the environment is restored even when an exception is raised
    """

    # Set an initial value for TEMP_VAR
    os.environ["TEMP_VAR"] = "initial_value"

    # Function that raises an exception
    @preserve_os_env
    def function_with_exception():
        os.environ["TEMP_VAR"] = "changed_value"
        raise ValueError("An error occurred")

    with pytest.raises(ValueError):
        function_with_exception()

    # Ensure the environment variable is restored after the exception
    assert os.environ.get("TEMP_VAR") == "initial_value"


def test_other_env_vars_not_affected():
    """
    Ensure that no other environment variables are affected
    """

    # Set initial values for multiple environment variables
    os.environ["VAR1"] = "value1"
    os.environ["VAR2"] = "value2"

    # Decorated function that changes one variable
    @preserve_os_env
    def change_only_one():
        os.environ["VAR1"] = "changed_value"
        return os.environ["VAR1"]

    # Call the function
    result = change_only_one()

    # Ensure VAR1 is changed within the function
    assert result == "changed_value"
    # Ensure VAR2 is not affected
    assert os.environ["VAR2"] == "value2"
    # Ensure VAR1 is restored after the function execution
    assert os.environ["VAR1"] == "value1"


def test_decorator_no_env_change():
    """
    Test that the decorator works with functions that do not modify environment variables
    """

    # Set an initial value for TEMP_VAR
    os.environ["TEMP_VAR"] = "initial_value"

    # Function that doesn't modify any environment variables
    @preserve_os_env
    def function_that_does_not_modify_env():
        return "No changes"

    # Call the function
    result = function_that_does_not_modify_env()

    # Ensure the environment variable remains unchanged
    assert os.environ["TEMP_VAR"] == "initial_value"
    assert result == "No changes"


def test_new_variables_cleaned():
    """
    Test that the decorator works will also remove additionally added variables afterwards
    """

    # Set an initial value for TEMP_VAR
    os.environ["TEMP_VAR"] = "initial_value"

    # Function that doesn't modify any environment variables
    @preserve_os_env
    def function_that_adds_a_new_key():
        os.environ["NEW_KEY"] = "new_value"

    # Call the function
    _ = function_that_adds_a_new_key()

    with pytest.raises(KeyError):
        _ = os.environ["NEW_KEY"]

    # Ensure the environment variable remains unchanged
    assert os.environ["TEMP_VAR"] == "initial_value"
