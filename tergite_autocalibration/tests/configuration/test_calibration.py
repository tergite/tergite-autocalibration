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

from tergite_autocalibration.tests.utils.env import setup_test_env

setup_test_env()

from tergite_autocalibration.config.globals import CONFIG
from tergite_autocalibration.config.legacy import LEGACY_CONFIG


def test_calibration_config():
    assert len(CONFIG.run.qubits) == 5
    assert len(CONFIG.run.couplers) == 1
    assert CONFIG.run.target_node == "ro_amplitude_two_state_optimization"
    assert "resonator_spectroscopy" in LEGACY_CONFIG.user_samplespace.keys()
