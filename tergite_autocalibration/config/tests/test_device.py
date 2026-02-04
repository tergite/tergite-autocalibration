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

    out_attenuations = device_configuration.get_output_attenuations()
    assert out_attenuations["qubit"]["q00"] == 4
    assert out_attenuations["qubit"]["q01"] == 8
    assert out_attenuations["coupler"]["q00_q01"] == 12
    assert out_attenuations["resonator"]["q00"] == 18
    assert out_attenuations["resonator"]["q01"] == 18

    assert "q00" in device_configuration.qubits.keys()

    assert device_configuration.resonators["q00"]["VNA_frequency"] == 6.48213e9
    assert device_configuration.qubits["q00"]["VNA_f01_frequency"] == 3.848e9
    assert device_configuration.qubits["q00"]["VNA_f12_frequency"] == 3.592e9
