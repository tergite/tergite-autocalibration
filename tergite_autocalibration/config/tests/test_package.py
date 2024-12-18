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
import shutil

import pytest

from tergite_autocalibration.config.package import ConfigurationPackage
from tergite_autocalibration.tests.utils.fixtures import get_fixture_path


@pytest.fixture
def mock_toml_file(tmp_path):
    """
    Fixture to create a temporary mock TOML file
    """
    toml_content = """
    path_prefix = "config"
    [files]
    run_config = "run_config.toml"
    cluster_config = "cluster_config.toml"
    """
    toml_file = tmp_path / "configuration.meta.toml"
    toml_file.write_text(toml_content)
    return toml_file


@pytest.fixture
def mock_toml_file_without_files_keyword(tmp_path):
    """
    Fixture to create a temporary mock TOML file
    """
    toml_content = """
    path_prefix = "config"
    """
    toml_file = tmp_path / "configuration.meta.toml"
    toml_file.write_text(toml_content)
    return toml_file


@pytest.fixture
def mock_toml_file_without_path_prefix_keyword(tmp_path):
    """
    Fixture to create a temporary mock TOML file
    """
    toml_content = """
    [files]
    run_config = "run_config.toml"
    cluster_config = "cluster_config.toml"
    """
    toml_file = tmp_path / "configuration.meta.toml"
    toml_file.write_text(toml_content)
    return toml_file


def test_from_toml_valid(mock_toml_file):
    """
    Test for the successful initialization from a valid TOML file
    """
    package = ConfigurationPackage.from_toml(str(mock_toml_file))
    assert package.meta_path == str(mock_toml_file)
    assert package.config_files["run_config"] == str(
        mock_toml_file.parent / "config/run_config.toml"
    )
    assert package.config_files["cluster_config"] == str(
        mock_toml_file.parent / "config/cluster_config.toml"
    )


def test_from_toml_missing_files_key(mock_toml_file_without_files_keyword):
    """
    Test for missing 'files' key in the TOML file
    """
    with pytest.raises(KeyError):
        ConfigurationPackage.from_toml(str(mock_toml_file_without_files_keyword))


def test_from_toml_missing_path_prefix_key(mock_toml_file_without_path_prefix_keyword):
    """
    Test for missing 'path_prefix' key in the TOML file
    """
    with pytest.raises(KeyError):
        ConfigurationPackage.from_toml(str(mock_toml_file_without_path_prefix_keyword))


@pytest.fixture
def mock_default_device_under_test_package_zip_path():
    """
    Load the configuration package as zip file from the fixtures
    """
    zip_path = get_fixture_path(
        "templates", "import_configuration_package_from_zip.zip"
    )
    unzip_path = get_fixture_path("templates", "import_configuration_package_from_zip")
    yield zip_path, unzip_path
    shutil.rmtree(unzip_path)


def test_from_zip_valid(mock_default_device_under_test_package_zip_path):
    """Test for initializing a package from a ZIP archive."""
    # Unzip the mock zip file to a temporary directory

    zip_path = mock_default_device_under_test_package_zip_path[0]
    unzip_path = mock_default_device_under_test_package_zip_path[1]

    package = ConfigurationPackage.from_zip(str(zip_path))
    assert package.meta_path == str(os.path.join(unzip_path, "configuration.meta.toml"))
    assert package.config_files["run_config"] is not None
    assert package.config_files["cluster_config"] is not None


@pytest.fixture
def mock_default_device_under_test_package_to_copy():
    """
    Load the configuration package in fixtures
    """
    destination_path = get_fixture_path("templates", "copied_package")
    meta_config_path = get_fixture_path(
        "templates", "default_device_under_test", "configuration.meta.toml"
    )
    yield destination_path, ConfigurationPackage.from_toml(meta_config_path)
    shutil.rmtree(destination_path)


def test_copy_creates_new_package(mock_default_device_under_test_package_to_copy):
    """
    Test the copy method for the ConfigurationPackage
    """
    destination_path = mock_default_device_under_test_package_to_copy[0]
    package = mock_default_device_under_test_package_to_copy[1]

    # Perform the copy
    new_package = package.copy(str(destination_path))

    # Check if the directory exists
    assert os.path.isdir(destination_path)

    # Check if the meta configuration file was copied
    assert os.path.isfile(os.path.join(destination_path, "configuration.meta.toml"))

    # Check if the config file was copied
    assert os.path.isfile(os.path.join(destination_path, "configs", "run_config.toml"))

    # Check if the misc folder was copied
    assert os.path.isdir(os.path.join(destination_path, "misc"))

    # Verify the new ConfigurationPackage instance points to the correct new paths
    assert new_package.meta_path == str(
        os.path.join(destination_path, "configuration.meta.toml")
    )
    assert new_package.config_files["run_config"] == str(
        os.path.join(destination_path, "configs", "run_config.toml")
    )
    assert new_package.misc_filepaths["miscellaneous_files"] == str(
        os.path.join(destination_path, "misc")
    )


def test_copy_creates_new_instance(mock_default_device_under_test_package_to_copy):
    """
    Test that the returned ConfigurationPackage instance is correctly initialized
    """
    destination_path = mock_default_device_under_test_package_to_copy[0]
    package = mock_default_device_under_test_package_to_copy[1]

    # Perform the copy
    new_package = package.copy(str(destination_path))

    # Ensure the returned ConfigurationPackage instance is a new object
    assert new_package is not mock_default_device_under_test_package_to_copy


@pytest.fixture
def mock_default_device_under_test_package_to_delete(
    mock_default_device_under_test_package_to_copy,
):
    """
    This is creating a copy of our fixture to not delete the original template
    """
    destination_path = mock_default_device_under_test_package_to_copy[0]
    package = mock_default_device_under_test_package_to_copy[1]

    # Perform the copy
    yield destination_path, package.copy(str(destination_path))


def test_delete_config_files(mock_default_device_under_test_package_to_delete):
    """
    Test the deletion of configuration files
    """
    package = mock_default_device_under_test_package_to_delete[1]

    # Check that files exist before deletion
    assert os.path.isfile(package.meta_path)
    assert os.path.isfile(package.config_files["run_config"])
    assert os.path.isdir(package.misc_filepaths["miscellaneous_files"])

    # Perform deletion
    package._delete_config_files()

    # Check that the config files were deleted
    assert not os.path.isfile(package.meta_path)
    assert not os.path.isfile(package.config_files["run_config"])

    # Check that the misc folder is still there (as we didn't delete it yet)
    assert os.path.isdir(package.misc_filepaths["miscellaneous_files"])


def test_delete_misc_files(mock_default_device_under_test_package_to_delete):
    """Test the deletion of misc files."""

    package = mock_default_device_under_test_package_to_delete[1]

    assert os.path.isdir(package.misc_filepaths["miscellaneous_files"])

    # Perform deletion
    package._delete_misc_files()

    # Check that the misc folder was deleted
    assert not os.path.isdir(package.misc_filepaths["miscellaneous_files"])
