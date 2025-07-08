# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from tergite_autocalibration.config.device import DeviceConfiguration
from tergite_autocalibration.config.handler import ConfigurationHandler
from tergite_autocalibration.config.package import ConfigurationPackage
from tergite_autocalibration.tests.utils.fixtures import get_fixture_path


def test_device_configuration():
    configuration_handler = ConfigurationHandler.from_configuration_package(
        ConfigurationPackage.from_toml(
            get_fixture_path(
                "templates", "default_device_under_test", "configuration.meta.toml"
            )
        )
    )

    device_configuration: DeviceConfiguration = configuration_handler.device
    assert device_configuration.name == "25-qubit FC8a #1"
