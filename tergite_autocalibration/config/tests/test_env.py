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
import tempfile
from pathlib import Path

import pytest
from dotenv import dotenv_values

from tergite_autocalibration.config.env import EnvironmentConfiguration
from tergite_autocalibration.tests.utils.decorators import preserve_os_env


@pytest.fixture
def mock_env_file():
    """Fixture to create a temporary .env file."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_env:
        temp_env.write(b"ROOT_DIR=/some/path\nREDIS_PORT=1234\nPLOTTING=true")
        temp_env.flush()
        yield temp_env.name
    os.unlink(temp_env.name)  # Cleanup after test


@preserve_os_env
@pytest.fixture
def env_config_instance():
    """Fixture for creating an instance of EnvironmentConfiguration."""
    return EnvironmentConfiguration()


@preserve_os_env
def test_initialization(env_config_instance):
    """Test that the EnvironmentConfiguration instance is initialized correctly."""
    assert isinstance(env_config_instance.root_dir, Path)
    assert isinstance(env_config_instance.data_dir, Path)
    assert isinstance(env_config_instance.config_dir, Path)
    assert env_config_instance.redis_port == 6379
    assert env_config_instance.plotting is False


@preserve_os_env
def test_from_dot_env_loads_environment(mock_env_file):
    """Test that values from the .env file are loaded into the environment."""
    config = EnvironmentConfiguration.from_dot_env(
        filepath=mock_env_file, write_env=False
    )

    assert os.environ["ROOT_DIR"] == "/some/path"
    assert os.environ["REDIS_PORT"] == "1234"
    assert os.environ["PLOTTING"] == "true"

    assert config.root_dir == "/some/path"
    assert config.redis_port == 1234
    assert config.plotting is True


@preserve_os_env
def test_from_dot_env_raises_if_file_not_found():
    """Test that an error is raised when the .env file does not exist."""
    with pytest.raises(EnvironmentError):
        EnvironmentConfiguration.from_dot_env(filepath="/non/existent/path.env")


@preserve_os_env
def test_write_env_updates_file(mock_env_file):
    """Test that updating an attribute writes to the .env file when _write_env is enabled."""
    config = EnvironmentConfiguration.from_dot_env(
        filepath=mock_env_file, write_env=True
    )
    config.redis_port = 5678
    config.plotting = False

    # Reload .env to confirm changes
    env_values = dotenv_values(mock_env_file)
    assert env_values["REDIS_PORT"] == "5678"
    assert env_values["PLOTTING"] == "False"


@preserve_os_env
def test_setattr_without_write_env(mock_env_file):
    """Test that updating an attribute does not write to the .env file when _write_env is disabled."""
    config = EnvironmentConfiguration.from_dot_env(
        filepath=mock_env_file, write_env=False
    )
    config.redis_port = 5678

    # Reload .env to confirm no changes
    env_values = dotenv_values(mock_env_file)
    assert env_values["REDIS_PORT"] == "1234"  # Original value


@preserve_os_env
def test_invalid_attribute_does_not_write(mock_env_file):
    """Test that updating an attribute not in __init__ does not write to the .env file."""
    config = EnvironmentConfiguration.from_dot_env(
        filepath=mock_env_file, write_env=True
    )

    # Add a new attribute dynamically
    config.new_attribute = "unexpected_value"

    # Reload .env to confirm no changes to the file
    env_values = dotenv_values(mock_env_file)
    assert "NEW_ATTRIBUTE" not in env_values
