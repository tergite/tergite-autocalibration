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
from pathlib import Path

import redis

from tergite_autocalibration.config.env import EnvironmentConfiguration
from tergite_autocalibration.config.handler import ConfigurationHandler
from tergite_autocalibration.config.package import ConfigurationPackage
from tergite_autocalibration.utils.misc.tests import is_pytest

# Loads the environmental configuration
#
# If there is a test going on, load the standard environment configuration.
# If you intentionally want to change environmental variables in a test, please take a look at the
# decorators implemented in tergite_autocalibration.tests.utils.decorators
if is_pytest():
    # Take the .env file from the folder for fixtures in the tests
    ENV = EnvironmentConfiguration.from_dot_env(
        filepath=os.path.join(
            str(Path(__file__).parent.parent),
            "tests",
            "fixtures",
            "configs",
            "env",
            "default.env",
        )
    )
else:
    # Try to load the .env file from the default locations
    ENV = EnvironmentConfiguration.from_dot_env()

# Creates a redis instance
REDIS_CONNECTION = redis.Redis(decode_responses=True, port=ENV.redis_port)

# This will be set in matplotlib
PLOTTING_BACKEND = "tkagg" if ENV.plotting else "agg"

# If there is no configuration package loaded, this would throw an error
try:
    if is_pytest():
        # Create the ConfigurationHandler from the default_device_under_test template in the fixtures
        CONFIG = ConfigurationHandler.from_configuration_package(
            ConfigurationPackage.from_toml(
                os.path.join(
                    str(Path(__file__).parent.parent),
                    "tests",
                    "fixtures",
                    "templates",
                    "default_device_under_test",
                    "configuration.meta.toml",
                )
            )
        )
    else:
        # Create the ConfigurationHandler from the meta configuration in the root directory
        CONFIG = ConfigurationHandler.from_configuration_package(
            ConfigurationPackage.from_toml(
                os.path.join(ENV.config_dir, "configuration.meta.toml")
            )
        )

# In the exception case we create an empty configuration package
except FileNotFoundError:
    CONFIG = ConfigurationPackage()
    logging.warning(
        "Default configuration is not yet loaded. "
        "Please copy configuration files to the root_directory or run `acli config load`."
    )

# NOTE: The cluster IP right now is passed only as a single value. For bigger setups with more than
#       one cluster it might make sense to store the cluster ip somewhere else. As of now, there is no
#       field in the hardware options of the QBLOX hardware configuration that would handle the ip.
CLUSTER_IP = ENV.cluster_ip

# The data directory where plots and results are saved
# Default is a folder called 'out' on the root level of the repository
DATA_DIR = ENV.data_dir

# If the data directory does not exist, it will be created automatically
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    logging.info(f"Initialised DATA_DIR -> {DATA_DIR}")
