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
import os.path

from tergite_autocalibration.tests.utils.fixtures import get_fixture_path
from tergite_autocalibration.tools.debug.start_calibration_supervisor import DebugConfiguration

def test_debugging_endpoint():

    debug_config_path = os.path.join(get_fixture_path(), "configs", "debug.toml")

    debug_config = DebugConfiguration(debug_config_path)

    assert debug_config.cluster_ip == "127.0.0.1"
    assert debug_config.dummy_cluster == False
    assert debug_config.reanalyse is None
    assert debug_config.node_name == "resonator_spectroscopy"
    assert debug_config.push == False
    assert debug_config.browser == True