# This code is part of Tergite
#
# (C) Copyright Michele Faucci Giannelli 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


import pytest
from tergite_autocalibration.lib.nodes.readout.punchout.node import (
    PunchoutNode,
)


@pytest.skip(
    "Skipping test for PunchoutNode as it requires a full Tergite environment."
)
def test_punchout_node_analysis_can_be_initialized():
    node_analysis = PunchoutNode("name", ["measure:pulse_amp"])

    assert node_analysis.name == "name"
    assert node_analysis.redis_fields == ["measure:pulse_amp"]
