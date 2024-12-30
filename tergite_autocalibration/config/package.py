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

import logging
import os
import shutil
from typing import Dict, Union

from tomlkit import parse, TOMLDocument


class ConfigurationPackage:
    """
    A package to bundle configuration files.
    When developing the package itself, please think of the functionality as similar as possible to a .zip archive.
    """

    def __init__(self):
        # Path to the standardised configuration.meta.toml file
        self.meta_path = None
        # The configuration files are not stored in here directly, but just passed as strings of the path
        # This allows the file to be more lightweight and having a behaviour similar to pointers in C.
        self.config_files: Dict[str, Union[str, None]] = {
            "run_config": None,
            "cluster_config": None,
            "device_config": None,
            "spi_config": None,
            "node_config": None,
            "user_samplespace": None,
        }
        self.misc_filepaths = {}

    @staticmethod
    def _validate_toml_file_content(file_content: TOMLDocument) -> bool:
        """
        Check whether the .toml file is valid

        Args:
            file_content: The loaded content from the .toml file

        Returns:
            True if the configuration file is having all the mandatory paramters

        """
        if "path_prefix" not in file_content.keys():
            raise KeyError(
                "The 'path_prefix' key is missing in the provided configuration.meta.toml file."
            )
        if "files" not in file_content.keys():
            raise KeyError(
                "The 'path_prefix' key is missing in the provided configuration.meta.toml file."
            )
        return True

    @staticmethod
    def from_toml(meta_config_path: str) -> "ConfigurationPackage":
        """
        Initialize a configuration package from its configuration.meta.toml file

        Args:
            meta_config_path: Path to the configuration.meta.toml file

        Returns:
            The initialized `ConfigurationPackage`

        """

        # Create a MetaConfiguration instance to be returned
        return_obj = ConfigurationPackage()

        # Check whether the .toml file exists
        if os.path.isfile(meta_config_path):
            return_obj.meta_path = meta_config_path

            # Parse the .toml file as dict
            with open(meta_config_path, "r") as f:
                meta_config = parse(f.read())

            # Validate the file structure of the .toml file
            assert ConfigurationPackage._validate_toml_file_content(meta_config)

            # Get the correct path to the configuration package to reconstruct relative paths
            meta_config_directory, _ = os.path.split(meta_config_path)
            config_path_prefix = os.path.join(
                meta_config_directory, meta_config["path_prefix"]
            )

            # Iterate over the possible config files
            for file_key_ in return_obj.config_files.keys():
                # Check whether the files exist in the meta configuration file
                if file_key_ in meta_config["files"].keys():
                    # Set the filepaths in the attribute
                    logging.info(
                        f"Loading {file_key_}: {meta_config['files'][file_key_]}"
                    )
                    return_obj.config_files[file_key_] = os.path.join(
                        config_path_prefix, meta_config["files"][file_key_]
                    )

            # Add the misc filepaths to the package
            if "misc" in meta_config.keys():
                for misc_key_, misc_path_ in meta_config["misc"].items():
                    return_obj.misc_filepaths[misc_key_] = os.path.join(
                        meta_config_directory, misc_path_
                    )

            logging.info(f"Loaded configuration package from {meta_config_path}")
            return return_obj

        else:
            raise FileNotFoundError(
                "Please provide a path to a configuration.meta.toml file."
            )

    @staticmethod
    def from_zip(meta_config_zip_path: str) -> "ConfigurationPackage":
        """
        Create a configuration package from a .zip archive.
        This will unzip the archive and read the configuration.meta.toml file

        Args:
            meta_config_zip_path: Path to the .zip archive

        Returns:

        """

        # Unzip the archive in the way it works on macOS such that it creates a folder with the same name
        meta_config_folder_path = os.path.splitext(meta_config_zip_path)[0]
        logging.info(
            f"Unpacking configuration package from {meta_config_zip_path} to {meta_config_folder_path}"
        )
        shutil.unpack_archive(meta_config_zip_path, meta_config_folder_path)

        # Load the configuration from the .toml file inside
        return ConfigurationPackage.from_toml(
            os.path.join(meta_config_folder_path, "configuration.meta.toml")
        )

    def move(self, to: str) -> "ConfigurationPackage":
        """
        Move a configuration package to another location.

        Args:
            to: Location to move the configuration package to

        Returns:

        """
        # Copy the configuration to the new location
        moved_configuration = self.copy(to)
        # Cleanup the old location
        self._delete_config_files()

        # For convenience make the current meta configuration object refer to the new paths
        self.config_files = moved_configuration.config_files
        self.meta_path = moved_configuration.meta_path
        return self

    def copy(self, to: str) -> "ConfigurationPackage":
        """
        Copy a configuration package to another location.

        Args:
            to: Location to copy the configuration package to

        Returns:
            An instance of the new copy of `ConfigurationPackage`

        """

        # Get the absolute path to where to copy and create the destination directory
        abs_path_to = os.path.abspath(to)
        os.makedirs(abs_path_to, exist_ok=True)

        # Construct the path to the new meta configuration
        new_path_to_meta = os.path.join(abs_path_to, "configuration.meta.toml")

        # Extract the old path to the meta configuration, because we need it to copy the files
        old_path_to_meta, _ = os.path.split(self.meta_path)
        # Adjust the meta config with the new paths
        shutil.copy(self.meta_path, new_path_to_meta)

        # Iterate over all configuration file paths
        for file_path in self.config_files.values():
            # Get the relative path from the current meta configuration to the file
            rel_path = os.path.relpath(file_path, old_path_to_meta)
            # Then create the new path to the location
            new_file_path = os.path.join(abs_path_to, rel_path)
            # Ensure that the parent directory exists
            os.makedirs(os.path.split(new_file_path)[0], exist_ok=True)
            # Copy the file to the new directory
            logging.info(f"Copying: \n" f"{file_path} \n" f"-> {new_file_path}")
            shutil.copy(file_path, new_file_path)

        # Iterate over all misc folders and copy them
        for misc_filepath in self.misc_filepaths.values():
            # Get the relative path from the current meta configuration to the misc folder
            rel_path = os.path.relpath(misc_filepath, old_path_to_meta)
            # Then create the new path to the location
            new_filepath = os.path.join(str(abs_path_to), str(rel_path))
            # Copy the whole folder to the new location
            if os.path.exists(new_filepath):
                logging.warning(
                    f"Location {new_filepath} already exists for the configuration package to copy. "
                    f"The files will not be copied to avoid conflicts. "
                    f"Please rename {misc_filepath} if you want to have the folder copied."
                )
            else:
                logging.info(f"Copying: \n" f"{misc_filepath} \n" f"-> {new_filepath}")
                shutil.copytree(misc_filepath, new_filepath, dirs_exist_ok=True)

        return ConfigurationPackage.from_toml(new_path_to_meta)

    def _delete_config_files(self, include_meta: bool = True):
        """
        Helper function to delete the configuration files within a configuration package.

        Args:
            include_meta: Whether the configuration.meta.toml should be deleted as well

        Returns:

        """

        file_paths = list(self.config_files.values())
        if include_meta:
            file_paths += [self.meta_path]

        for file_path in file_paths:
            try:
                logging.info(f"Deleting {file_path}")
                os.remove(file_path)
            except FileNotFoundError:
                logging.error(f"Config file '{file_path}' not found.")
            except PermissionError:
                logging.error(
                    f"Permission denied to delete the config file '{file_path}'."
                )
            except Exception as e:
                logging.error(f"An error occurred: {e}")

    def _delete_misc_files(self):
        """
        Helper function to delete the configuration files within a configuration package.
        """

        file_paths = list(self.misc_filepaths.values())

        for file_path in file_paths:
            try:
                logging.info(f"Deleting {file_path}")
                shutil.rmtree(file_path)
            except FileNotFoundError:
                logging.error(f"Folder '{file_path}' not found.")
            except PermissionError:
                logging.error(f"Permission denied to delete the folder '{file_path}'.")
            except Exception as e:
                logging.error(f"An error occurred: {e}")

    def delete(self):
        """
        Delete a configuration package.

        Returns:

        """
        self._delete_misc_files()
        self._delete_config_files()
        del self
