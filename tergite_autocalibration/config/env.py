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
import logging
import os
from pathlib import Path
from typing import Union

from dotenv import dotenv_values, set_key

from tergite_autocalibration.config.base import BaseConfigurationFile
from tergite_autocalibration.utils.misc.regex import is_bool, str_to_bool
from tergite_autocalibration.utils.reflections import ASTParser


class EnvironmentConfiguration(BaseConfigurationFile):
    _write_env: bool = False

    def __init__(self):
        super().__init__("")

        # NOTE: For all the variables set here, it is important that they are the lower case version
        # of the respective variable in the .env file. E.g.:
        # self.root_dir refers to ROOT_DIR in the .env file
        # If this convention is not followed, it is not possible to automatically update the .env file
        # through the getters and setters.

        self.default_prefix: str = getpass.getuser().replace(" ", "")

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
        filepath: Union[str, Path] = Path(__file__).parent.parent.parent.joinpath(
            ".env"
        ),
        write_env: bool = False,
    ):
        """
        Load the values from the .env file actually into the os environment.

        Args:
            filepath: Path to the .env file. Can be overwritten by setting an environment variable
                      called `TAC_TEST_ENV_FILEPATH`. Then the environment will be loaded from that
                      location instead.
            write_env: If write_env is set to true, then values that are written to this configuration
                      will be written to the .env file. Can be also set in the .env file itself.

        Returns:
            An instance of `EnvironmentConfiguration` which has all values from the environment set.

        """
        return_obj = EnvironmentConfiguration()
        return_obj._write_env = write_env

        # Check whether the .env file exists
        if not os.path.exists(filepath):
            raise EnvironmentError("The .env file configuration cannot be found.")

        # Then write the filepath also to the return object, so, it can be used later on
        return_obj.filepath = filepath

        # Load the .env file and propagate the values into the environment
        logging.info(f"Loading .env values from {filepath}")
        env_values_ = dotenv_values(filepath)
        for env_key_, env_value_ in env_values_.items():
            os.environ[env_key_] = env_value_

        # Iterate over the variables in the constructor and set them from the environment
        for variable_name_ in ASTParser.get_init_attribute_names(
            EnvironmentConfiguration
        ):
            if variable_name_.upper() in os.environ:
                variable_value_ = os.environ[variable_name_.upper()]
                # Convert boolean string to actual boolean
                # Note: This could be elaborated and use generic typing from the annotations in __init__
                if is_bool(variable_value_):
                    return_obj.__setattr__(variable_name_, str_to_bool(variable_value_))
                else:
                    return_obj.__setattr__(variable_name_, variable_value_)

        return return_obj

    def __setattr__(self, key_, value_):
        # Write the changes to the .env file directly
        if (
            key_ in ASTParser.get_init_attribute_names(EnvironmentConfiguration)
            and self._write_env
        ):
            if self.filepath is not None:
                set_key(self.filepath, key_.upper(), str(value_))

        # Delegate to the base class for all other cases
        super().__setattr__(key_, value_)
