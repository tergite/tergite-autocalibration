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

import json

from quantify_scheduler.backends.qblox_backend import QbloxHardwareCompilationConfig

from tergite_autocalibration.config.device import DeviceConfiguration
from tergite_autocalibration.config.node import NodeConfiguration
from tergite_autocalibration.config.package import ConfigurationPackage
from tergite_autocalibration.config.run import RunConfiguration
from tergite_autocalibration.config.samplespace import SamplespaceConfiguration
from tergite_autocalibration.config.spi import SpiConfiguration


class ConfigurationHandler:
    """
    Class to handle all configuration that exist there
    """

    def __init__(self):
        self.run: "RunConfiguration"
        self.samplespace: "SamplespaceConfiguration"
        self.cluster: "QbloxHardwareCompilationConfig"

        # TODO: The format for the configurations below is as of now not yet well-defined on the backend side
        self.device: "DeviceConfiguration"
        self.node: "NodeConfiguration"
        self.spi: "SpiConfiguration"

    @staticmethod
    def from_configuration_package(
        configuration_package: "ConfigurationPackage",
    ) -> "ConfigurationHandler":
        """
        Initializes a `ConfigurationHandler` from a `ConfigurationPackage`.

        Args:
            configuration_package: The configuration package to import

        Returns:

        """
        return_obj = ConfigurationHandler()

        return_obj.run = RunConfiguration(
            configuration_package.config_files["run_config"]
        )
        return_obj.samplespace = SamplespaceConfiguration(
            configuration_package.config_files["user_samplespace"]
        )

        # Loading the QBLOX cluster configuration
        # This should be wrapped as little as possible to reduce the amount of work if there
        # are changes on the quantify/qblox side.
        with open(configuration_package.config_files["cluster_config"], "r") as f_:
            cluster_config_json = json.load(f_)
            return_obj.cluster = QbloxHardwareCompilationConfig.model_validate(
                cluster_config_json
            )

        return_obj.device = DeviceConfiguration(
            configuration_package.config_files["device_config"]
        )
        return_obj.spi = configuration_package.config_files["spi_config"]
        return_obj.node = configuration_package.config_files["node_config"]

        return return_obj
