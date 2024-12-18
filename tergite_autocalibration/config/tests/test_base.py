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

from pathlib import Path

import pytest
import toml

from tergite_autocalibration.config.base import (
    BaseConfigurationFile,
    TOMLConfigurationFile,
)


class TestConfigurationFile(BaseConfigurationFile):
    """A concrete implementation for testing purposes"""

    pass


@pytest.fixture
def sample_filepath():
    """Fixture to provide a sample filepath."""
    return "test_config.json"


@pytest.fixture
def base_config(sample_filepath):
    """Fixture to create a BaseConfigurationFile instance."""
    return TestConfigurationFile(filepath=sample_filepath)


def test_filepath_getter_and_setter(base_config, sample_filepath):
    """Test getter and setter for filepath."""
    # Check initial filepath
    assert base_config.filepath == Path(sample_filepath)

    # Update the filepath and verify
    new_filepath = "new_config.json"
    base_config.filepath = new_filepath
    assert base_config.filepath == Path(new_filepath)


def test_filepath_accepts_pathlib_path(base_config):
    """Test if the filepath accepts Path objects."""
    new_filepath = Path("pathlib_config.json")
    base_config.filepath = new_filepath
    assert base_config.filepath == new_filepath


def test_initialization_with_path_object():
    """Test initialization with a Path object."""
    path_obj = Path("path_object_config.json")
    config_instance = TestConfigurationFile(filepath=path_obj)
    assert config_instance.filepath == path_obj


def test_filepath_invalid_type():
    """Test setting an invalid type for filepath."""
    config_instance = TestConfigurationFile(filepath="valid_path.json")
    with pytest.raises(TypeError):
        config_instance.filepath = 123


@pytest.fixture
def sample_toml_file(tmp_path):
    """
    Fixture to create a sample .toml file.
    """
    sample_data = {
        "q00": {
            "frequency": 1,
            "amplitude": 2,
            "motzoi": 0,
            "comment": "very low coherence time",
        },
        "q01": {"frequency": 1, "amplitude": 2, "measured": True},
    }
    filepath = tmp_path / "config.toml"
    with open(filepath, "w") as f:
        toml.dump(sample_data, f)
    return filepath, sample_data


@pytest.fixture
def toml_config(sample_toml_file):
    """
    Fixture to create a TOMLConfigurationFile instance.
    """
    filepath, _ = sample_toml_file
    return TOMLConfigurationFile(filepath=filepath)


def test_toml_file_loading(toml_config, sample_toml_file):
    """
    Test that the .toml file is loaded into _dict correctly.
    """
    _, expected_data = sample_toml_file
    assert toml_config._dict == expected_data


def test_access_nested_values(toml_config):
    """
    Test accessing nested values in the .toml data.
    """
    assert toml_config._dict["q00"]["frequency"] == 1
    assert toml_config._dict["q00"]["comment"] == "very low coherence time"
    assert toml_config._dict["q01"]["measured"] is True


def test_invalid_toml_file(tmp_path):
    """
    Test loading an invalid .toml file.
    """
    invalid_filepath = tmp_path / "invalid_config.toml"
    invalid_filepath.write_text("invalid: toml: content")

    with pytest.raises(toml.TomlDecodeError):
        TOMLConfigurationFile(filepath=invalid_filepath)


def test_file_does_not_exist():
    """
    Test handling a non-existent file.
    """
    with pytest.raises(FileNotFoundError):
        TOMLConfigurationFile(filepath="non_existent_config.toml")
