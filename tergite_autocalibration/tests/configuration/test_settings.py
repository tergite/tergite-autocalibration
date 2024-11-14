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
from ipaddress import IPv4Address
from pathlib import Path

from tergite_autocalibration.tests.utils.env import (
    setup_test_env,
    TEST_ROOT_DIR,
    TEST_DATA_DIR,
    TEST_CONFIG_DIR,
    TEST_CLUSTER_CONFIG,
    TEST_SPI_CONFIG,
    TEST_DEVICE_CONFIG,
    TEST_RUN_CONFIG,
    TEST_NODE_CONFIG,
    TEST_USER_SAMPLESPACE,
    TEST_CLUSTER_IP,
    TEST_SPI_SERIAL_PORT,
    TEST_REDIS_PORT,
    TEST_PLOTTING,
)

setup_test_env()

from tergite_autocalibration.config.settings import (
    ROOT_DIR,
    DATA_DIR,
    CONFIG_DIR,
    RUN_CONFIG,
    CLUSTER_CONFIG,
    SPI_CONFIG,
    DEVICE_CONFIG,
    NODE_CONFIG,
    USER_SAMPLESPACE,
    CLUSTER_IP,
    SPI_SERIAL_PORT,
    REDIS_PORT,
    PLOTTING,
)


def test_global_variables():
    # This is a quick sanity check whether the test environment setup work itself
    assert ROOT_DIR == Path(TEST_ROOT_DIR)
    assert DATA_DIR == Path(TEST_DATA_DIR)
    assert CONFIG_DIR == Path(TEST_CONFIG_DIR)

    assert RUN_CONFIG == Path(os.path.join(CONFIG_DIR, TEST_RUN_CONFIG))
    assert CLUSTER_CONFIG == Path(os.path.join(CONFIG_DIR, TEST_CLUSTER_CONFIG))
    assert SPI_CONFIG == Path(os.path.join(CONFIG_DIR, TEST_SPI_CONFIG))
    assert DEVICE_CONFIG == Path(os.path.join(CONFIG_DIR, TEST_DEVICE_CONFIG))
    assert NODE_CONFIG == Path(os.path.join(CONFIG_DIR, TEST_NODE_CONFIG))
    assert USER_SAMPLESPACE == Path(os.path.join(CONFIG_DIR, TEST_USER_SAMPLESPACE))

    assert CLUSTER_IP == IPv4Address(TEST_CLUSTER_IP)
    assert SPI_SERIAL_PORT == TEST_SPI_SERIAL_PORT

    assert REDIS_PORT == int(TEST_REDIS_PORT)

    assert PLOTTING == eval(TEST_PLOTTING)
