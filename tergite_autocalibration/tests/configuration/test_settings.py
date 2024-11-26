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

from tergite_autocalibration.config.env import EnvironmentConfiguration
from tergite_autocalibration.config.globals import ENV, CONFIG
from tergite_autocalibration.config.handler import ConfigurationHandler
from tergite_autocalibration.config.package import ConfigurationPackage
from tergite_autocalibration.tests.utils.fixtures import get_fixture_path


def test_global_env_configuration():

    env_configuration = EnvironmentConfiguration.from_dot_env(
        get_fixture_path("configs", "env", "default.env")
    )

    assert ENV.default_prefix == env_configuration.default_prefix

    assert ENV.root_dir == env_configuration.root_dir
    assert ENV.data_dir == env_configuration.data_dir
    assert ENV.config_dir == env_configuration.config_dir

    assert ENV.backend_config == env_configuration.backend_config

    assert ENV.cluster_ip == env_configuration.cluster_ip
    assert ENV.spi_serial_port == env_configuration.spi_serial_port

    assert ENV.redis_port == env_configuration.redis_port
    assert ENV.plotting == env_configuration.plotting

    assert ENV.mss_machine_root_url == env_configuration.mss_machine_root_url


def test_global_configuration():
    configuration_handler = ConfigurationHandler.from_configuration_package(
        ConfigurationPackage.from_toml(
            get_fixture_path(
                "templates", "default_device_under_test", "configuration.meta.toml"
            )
        )
    )

    assert configuration_handler.run.filepath == CONFIG.run.filepath
    assert configuration_handler.samplespace.filepath == CONFIG.samplespace.filepath
