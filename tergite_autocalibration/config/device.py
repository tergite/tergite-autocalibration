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

from tergite_autocalibration.config.base import TOMLConfigurationFile
from tergite_autocalibration.utils.logging import logger


class DeviceConfiguration(TOMLConfigurationFile):
    """
    Configuration for the device
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Load the device part of the device configuration file
        try:
            self._device = self._dict["device"]
        except KeyError:
            logger.warning(
                "Device configuration empty or not found, please check your device configuration."
            )
            self._device = {}

    @property
    def name(self) -> str:
        """
        Returns:
            Name of the device

        """
        return self._device["name"]
