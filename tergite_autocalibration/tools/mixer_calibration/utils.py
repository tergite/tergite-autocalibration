# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs AB 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


from typing import Dict, Any


def replace_mixer_corrected_values(
    cluster_config: Dict[str, Any],
    mixer_corrected_values: Dict[str, Dict[str, float]],
) -> Dict[str, Any]:

    # Load mixer calibration values from cluster configuration file
    old_mixer_calibration_values = cluster_config["hardware_options"][
        "mixer_corrections"
    ]

    # replace mixer calibration values
    new_mixer_calibration_values = old_mixer_calibration_values | mixer_corrected_values
    cluster_config["hardware_options"][
        "mixer_corrections"
    ] = new_mixer_calibration_values

    return cluster_config
