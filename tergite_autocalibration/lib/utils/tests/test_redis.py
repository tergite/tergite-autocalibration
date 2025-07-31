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

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.lib.utils.redis import _save_parameters_in_transmon
from tergite_autocalibration.utils.dto.qoi import QOI


def test_save_parameters_in_transmon():
    """
    Base case e.g. after resonator spectroscopy
    """

    node = "resonator_spectroscopy"
    this_element = "q01"
    name = "transmons"
    analysis_result = {
        "resonator_minimum": {
            "value": 3.91e9,
            "error": 0.01,
        },
    }

    qoi = QOI(analysis_result, True)

    _save_parameters_in_transmon(node, this_element, name, qoi, ["resonator_minimum"])

    resonator_minimum_value = float(
        REDIS_CONNECTION.hget(f"{name}:{this_element}", "resonator_minimum")
    )
    assert resonator_minimum_value == 3.91e9

    resonator_minimum_value = float(
        REDIS_CONNECTION.hget(f"{name}:{this_element}", "resonator_minimum_error")
    )
    assert resonator_minimum_value == 0.01
