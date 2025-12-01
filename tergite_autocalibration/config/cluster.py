# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs AB 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


from quantify_scheduler.backends.qblox_backend import QbloxHardwareCompilationConfig

from tergite_autocalibration.config.base import BaseConfigurationFile


class ClusterConfiguration(QbloxHardwareCompilationConfig, BaseConfigurationFile):
    """
    A class to handle specific configurations for the cluster configuration

    This should be wrapped as little as possible to avoid big changes during quantify / qblox updates
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
