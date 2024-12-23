# This code is part of Tergite
#
# (C) Copyright Stefan Hill 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# ---
# This file contains all functionality related to the system settings and configuration.
# If you are adding variables, please make sure that they are upper case, because in the code, it should be
# clear that these variables are sort of global configuration environment variables

import getpass
import os
from pathlib import Path
from typing import Union

from dotenv import dotenv_values, set_key

from tergite_autocalibration.config.base import BaseConfigurationFile
from tergite_autocalibration.utils.misc.reflections import ASTParser
from tergite_autocalibration.utils.misc.types import safe_str_to_bool_int_float


def _get_default_env_path() -> Union[str, Path]:
    """
    This is a helper function to find the .env file

    Returns:
        Path to the default .env file

    """

    # Assume that the .env file is located in the root directory of the repository
    default_env_path_ = Path(__file__).parent.parent.parent.joinpath(".env")

    # If not, take it from the current working directory
    if not os.path.exists(default_env_path_):
        default_env_path_ = os.path.join(os.getcwd(), ".env")

    # If it still does not exist there, an error would be thrown later in the code when it is loaded
    return default_env_path_


class EnvironmentConfiguration(BaseConfigurationFile):
    """
    A class to .env file or create environment configurations from within the framework
    """

    # This variable is there to indicate whether the environment configuration should write values
    # that are set, directly to the .env file if one is specified. The use cases here would be e.g.
    # when you want to implement a function that changes the redis instance programmatically.
    _write_env: bool = False

    def __init__(self):
        super().__init__("")

        # NOTE: For all the variables set here, it is important that they are the lower case version
        # of the respective variable in the .env file. E.g.:
        # self.root_dir refers to ROOT_DIR in the .env file
        # If this convention is not followed, it is not possible to automatically update the .env file
        # through the getters and setters.

        self.default_prefix: str = getpass.getuser().replace(" ", "")

        self.file_log_level: int = 25
        self.stdout_log_level: int = 10

        self.root_dir: "Path" = Path(__file__).parent.parent.parent
        self.data_dir: "Path" = self.root_dir.joinpath("out")
        self.config_dir: "Path" = self.root_dir

        self.backend_config: "Path" = (
            Path(__file__).parent / "backend_config_default.toml"
        )

        self.cluster_ip: str = "0.0.0.0"
        self.spi_serial_port: str = "/dev/ttyACM0"

        self.redis_port: int = 6379
        self.plotting: bool = False

        self.mss_machine_root_url: str = "http://localhost:8002"

    @staticmethod
    def from_dot_env(
        filepath: Union[str, Path] = _get_default_env_path(),
        write_env: bool = False,
    ):
        """
        Load the values from the .env file actually into the os environment.

        Args:
            filepath: Path to the .env file. Then the environment will be loaded from that
                      location instead.
            write_env: If write_env is set to true, then values that are written to this configuration
                      will be written to the .env file. Can be also set in the .env file itself.

        Returns:
            An instance of `EnvironmentConfiguration` which has all values from the environment set.

        """
        # Note: The logger is imported locally to prevent circular dependencies.
        #       The circular dependency is introduced, because the log level can be set in the environmental variables.
        from tergite_autocalibration.config.globals import logger

        return_obj = EnvironmentConfiguration()
        return_obj._write_env = write_env

        # Check whether the .env file exists
        if not os.path.exists(filepath):
            raise EnvironmentError("The .env file configuration cannot be found.")

        # Then write the filepath also to the return object, so, it can be used later on
        return_obj.filepath = filepath

        # Load the .env file and propagate the values into the environment
        logger.info(f"Loading .env values from {filepath}")
        env_values_ = dotenv_values(filepath)
        for env_key_, env_value_ in env_values_.items():
            os.environ[env_key_] = env_value_

        # Iterate over the variables in the constructor and set them from the environment
        for variable_name_ in ASTParser.get_init_attribute_names(
            EnvironmentConfiguration
        ):
            if variable_name_.upper() in os.environ:

                # Get the variable value from the environment
                variable_value_ = os.environ[variable_name_.upper()]

                # Check which type the value should be
                expected_type_ = type(getattr(return_obj, variable_name_))

                # Cast the string value from the .env file to the expected type
                typed_variable_value_ = safe_str_to_bool_int_float(
                    expected_type_, variable_value_
                )

                logger.info(
                    f"Loading {variable_name_.upper()}: {typed_variable_value_}"
                )
                return_obj.__setattr__(variable_name_, typed_variable_value_)

        logger.info(f"Loaded environmental variables from {filepath}")
        return return_obj

    def __setattr__(self, key_, value_):
        # Write the changes to the .env file directly
        if (
            key_ in ASTParser.get_init_attribute_names(EnvironmentConfiguration)
            and self._write_env
            and self.filepath is not None
        ):
            set_key(self.filepath, key_.upper(), str(value_))

        # Delegate to the base class for all other cases
        super().__setattr__(key_, value_)
