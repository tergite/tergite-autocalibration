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

import json

from tergite_autocalibration.tests.utils.fixtures import get_fixture_path
from tergite_autocalibration.tools.mixer_calibration.utils import (
    replace_mixer_corrected_values,
)


def test_replace_mixer_corrected_values():
    """
    Basic test to check whether the function replaces the right values
    """

    # Copy cluster configuration to the temporary data path
    _cluster_config_path = get_fixture_path("configs", "cluster_config.json")

    with open(_cluster_config_path, "r") as f_:
        cluster_config = json.load(f_)

    mixer_corrected_values = {
        "q11:mw-q11.01": {
            "dc_offset_i": -0.0072251,
            "dc_offset_q": -0.0061963,
            "amp_ratio": 0.9986,
            "phase_error": 11.20603,
        },
        "q11:mw-q11.12": {
            "dc_offset_i": -0.0072251,
            "dc_offset_q": -0.0061963,
            "amp_ratio": 0.9986,
            "phase_error": 12.97026,
        },
    }

    # Make sure the cluster configuration is loaded correctly
    assert "clusterA" in cluster_config["hardware_description"].keys()
    # Check old mixer calibration values before replacement
    assert cluster_config["hardware_options"]["mixer_corrections"]["q11:mw-q11.01"] == {
        "amp_ratio": 0.9655,
        "dc_offset_i": -0.0095862,
        "dc_offset_q": -0.000955,
        "phase_error": -27.60144,
    }

    # Replace the mixer calibration values
    new_cluster_config = replace_mixer_corrected_values(
        cluster_config, mixer_corrected_values
    )

    # Check whether values got replaced
    assert (
        new_cluster_config["hardware_description"]
        == cluster_config["hardware_description"]
    )
    assert new_cluster_config["hardware_options"]["mixer_corrections"][
        "q11:mw-q11.01"
    ] == {
        "dc_offset_i": -0.0072251,
        "dc_offset_q": -0.0061963,
        "amp_ratio": 0.9986,
        "phase_error": 11.20603,
    }
