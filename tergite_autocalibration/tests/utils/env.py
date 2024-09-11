# This code is part of Tergite
#
# (C) Copyright Martin Ahindura 2024
# (C) Copyright Stefan Hill 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import os
from os import environ
from pathlib import Path

TEST_DEFAULT_PREFIX = "tergite-autocalibration-testing"
TEST_MSS_MACHINE_ROOT_URL = "http://localhost:8002"

TEST_ROOT_DIR = str(Path(__file__).parent.parent.parent.parent)
TEST_DATA_DIR = os.path.join(Path(__file__).parent.parent, "fixtures", "data")
TEST_CONFIG_DIR = os.path.join(Path(__file__).parent.parent, "fixtures", "configs")
TEST_HARDWARE_CONFIG = "hardware_config.json"
TEST_DEVICE_CONFIG = "device_config.toml"

TEST_CLUSTER_IP = "192.0.2.141"
TEST_CLUSTER_NAME = "clusterA"
TEST_SPI_SERIAL_PORT = "/dev/ttyACM0"

TEST_RUN_MODE = "test"

TEST_REDIS_PORT = "6379"
TEST_PLOTTING = "False"


def setup_test_env():
    """Sets up the test environment.

    It should be run before any imports
    """
    environ["DEFAULT_PREFIX"] = TEST_DEFAULT_PREFIX
    environ["MSS_MACHINE_ROOT_URL"] = TEST_MSS_MACHINE_ROOT_URL

    environ["ROOT_DIR"] = TEST_ROOT_DIR
    environ["DATA_DIR"] = TEST_DATA_DIR
    environ["CONFIG_DIR"] = TEST_CONFIG_DIR
    environ["HARDWARE_CONFIG"] = TEST_HARDWARE_CONFIG
    environ["DEVICE_CONFIG"] = TEST_DEVICE_CONFIG

    environ["CLUSTER_IP"] = TEST_CLUSTER_IP
    environ["CLUSTER_NAME"] = TEST_CLUSTER_NAME
    environ["SPI_SERIAL_PORT"] = TEST_SPI_SERIAL_PORT

    environ["RUN_MODE"] = TEST_RUN_MODE

    environ["REDIS_PORT"] = TEST_REDIS_PORT
    environ["PLOTTING"] = TEST_PLOTTING
