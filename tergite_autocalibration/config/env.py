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
from ipaddress import ip_address
from pathlib import Path
from typing import Union

from tergite_autocalibration.config.base import BaseConfigurationFile
from tergite_autocalibration.config.utils import from_environment
from tergite_autocalibration.utils.reflections import ASTParser


class EnvironmentConfiguration(BaseConfigurationFile):

    def __init__(self):
        super().__init__()

        self.default_prefix: str = getpass.getuser().replace(" ", "")

        self.root_dir: "Path" = Path(__file__).parent.parent.parent
        self.data_dir: "Path" = self.root_dir.joinpath("out")
        self.config_dir: "Path" = self.root_dir

        self.backend_config: "Path" = (
            Path(__file__).parent / "backend_config_default.toml"
        )

        self.cluster_ip: str
        self.spi_serial_port: str

        self.redis_port: int = 6379
        self.plotting: bool = True

        self.mss_machine_root_url: str = "http://localhost:8002"

    @staticmethod
    def from_dot_env(
        filepath: Union[str, Path] = Path(__file__).parent.parent.parent.joinpath(
            ".env"
        )
    ):
        return_obj = EnvironmentConfiguration()

        # Load .env file
        # Dump values into the environment
        # Then load them from the environment
        # We do not need to take care of the defaults any longer, because they are already set
        # We can get rid of the utils.py

        return return_obj

    def __setattr__(self, key_, value_):
        # Custom logic for attributes in _initialized_attributes
        if key_ in ASTParser.get_init_attribute_names(EnvironmentConfiguration):
            # We need a template file for the .env file
            pass

        # Delegate to the base class for all other cases
        super().__setattr__(key_, value_)


# ---
# Section with directory configurations

# Root directory of the project
ROOT_DIR = from_environment(
    "ROOT_DIR", cast_=Path, default=Path(__file__).parent.parent.parent
)

# Data directory to store plots and datasets
DATA_DIR = from_environment("DATA_DIR", cast_=Path, default=ROOT_DIR.joinpath("out"))

# If the data directory does not exist, it will be created automatically
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    logging.info(f"Initialised DATA_DIR -> {DATA_DIR}")

# Path to the definition of the configuration package
CONFIG_DIR = from_environment("CONFIG_DIR", cast_=Path, default=ROOT_DIR)

BACKEND_CONFIG = Path(__file__).parent / "backend_config_default.toml"

# ---
# Section with other configuration variables
CLUSTER_IP = ip_address(from_environment("CLUSTER_IP", cast_=str))
SPI_SERIAL_PORT = from_environment("SPI_SERIAL_PORT", cast_=str)

# ---
# Section for redis connectivity
REDIS_PORT = from_environment("REDIS_PORT", cast_=int, default=6379)

# ---
# Section for plotting
PLOTTING = from_environment("PLOTTING", cast_=bool, default=False)


# ---
# Section with connectivity definitions
MSS_MACHINE_ROOT_URL = from_environment(
    "MSS_MACHINE_ROOT_URL", cast_=str, default="http://localhost:8002"
)
