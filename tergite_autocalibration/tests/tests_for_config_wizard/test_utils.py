# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2025
# (C) Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from tergite_autocalibration.tools.hardware_config_wizard.utils import expand_range


def test_expand_range():
    input = "q01-q11"
    qubits = expand_range(input)
    assert len(qubits) == 11
    assert qubits[0] == "q01"
    assert qubits[-1] == "q11"
