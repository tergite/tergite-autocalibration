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
# If there is a test going on, load the standard environment configuration
# TODO: Add note about changing the configuration for a pytest with decorator
if is_pytest():
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
    ENV = EnvironmentConfiguration.from_dot_env()

# Creates a redis instance
REDIS_CONNECTION = redis.Redis(decode_responses=True, port=ENV.redis_port)

# This will be set in matplotlib
PLOTTING_BACKEND = "tkagg" if ENV.plotting else "agg"

CONFIG = ConfigurationHandler.from_configuration_package(
    ConfigurationPackage.from_toml(
        os.path.join(ENV.config_dir, "configuration.meta.toml")
    )
)

# TODO: To be factored out
CLUSTER_IP = ENV.cluster_ip

DATA_DIR = ENV.data_dir

# If the data directory does not exist, it will be created automatically
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    logging.info(f"Initialised DATA_DIR -> {DATA_DIR}")
