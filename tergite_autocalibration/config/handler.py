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
from typing import TYPE_CHECKING

from quantify_scheduler.backends.qblox_backend import QbloxHardwareCompilationConfig

from tergite_autocalibration.config.device import DeviceConfiguration
from tergite_autocalibration.config.node import NodeConfiguration
from tergite_autocalibration.config.run import RunConfiguration
from tergite_autocalibration.config.user_samplespace import UserSamplespaceConfiguration

if TYPE_CHECKING:
    from tergite_autocalibration.config.package import ConfigurationPackage


class ConfigurationHandler:

    def __init__(self):
        self.rc: "RunConfiguration" = RunConfiguration()
        # TODO: This configuration has to be replace with the actual device definition
        self.device: "DeviceConfiguration" = DeviceConfiguration()
        self.node: "NodeConfiguration" = NodeConfiguration()
        self.samplespace: "UserSamplespaceConfiguration" = (
            UserSamplespaceConfiguration()
        )
        self.cluster: "QbloxHardwareCompilationConfig"

    @staticmethod
    def from_configuration_package(
        configuration_package: "ConfigurationPackage",
    ) -> "ConfigurationHandler":
        return_obj = ConfigurationHandler()

        return_obj.rc = configuration_package.config_files["run_config"]
        return_obj.device = configuration_package.config_files["device_config"]
        return_obj.samplespace = configuration_package.config_files["user_samplespace"]

        with open(configuration_package.config_files["cluster_config"], "r") as f_:
            cluster_config_json = json.load(f_)
            return_obj.cluster_config = QbloxHardwareCompilationConfig.model_validate(
                cluster_config_json
            )

        return return_obj
