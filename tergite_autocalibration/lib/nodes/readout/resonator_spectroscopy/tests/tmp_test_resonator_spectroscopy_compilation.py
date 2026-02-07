# This code is part of Tergite
#
# (C) Chalmers Next Labs AB 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from tergite_autocalibration.lib.nodes.readout.resonator_spectroscopy.node import (
    ResonatorSpectroscopyNode,
)
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


def test_compile_measurement():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = ResonatorSpectroscopyNode("resonator_spectroscopy", ["q00", "q01"])
    compiled_schedule = node.precompile(node.schedule_samplespace)
    breakpoint()

    # Additionally to compiling without error, we can add assert statements to check the compiled schedule
