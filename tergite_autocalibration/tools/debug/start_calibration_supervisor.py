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

from ipaddress import IPv4Address

from tergite_autocalibration.config.globals import CLUSTER_IP
from tergite_autocalibration.scripts.calibration_supervisor import (
    CalibrationSupervisor,
    CalibrationConfig,
)
from tergite_autocalibration.utils.dto.enums import MeasurementMode

# Note: This script emulates the cli endpoint `acli calibration start`.
#
#       Before using the script, please read the section about debugging in the documentation
#       carefully. If you are running into any errors, please compare the code in tools/cli
#       to ensure that the code is the same as in the original endpoint.

if __name__ == '__main__':

    # Initialize the configuration
    cluster_mode: "MeasurementMode" = MeasurementMode.real
    parsed_cluster_ip: "IPv4Address" = CLUSTER_IP
    config = CalibrationConfig(cluster_mode=cluster_mode, cluster_ip=parsed_cluster_ip)

    # Initialize the supervisor and start the calibration
    supervisor = CalibrationSupervisor(config)
    supervisor.calibrate_system()
