# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2024
# (C) Copyright Michele Faucci Giannelli 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from tergite_autocalibration.config.base import TOMLConfigurationFile


class DeviceConfiguration(TOMLConfigurationFile):
    """
    Configuration for the device
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def name(self) -> str:
        """
        Returns:
            flag if the plots are for internal use or not.

        """
        return self._dict["device"]["name"]

    @property
    def owner(self) -> str:
        """
        Returns:
            Path to the logo to be used in the runner.

        """
        return self._dict["device"]["owner"]
