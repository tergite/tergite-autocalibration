# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2025
# (C) Chalmers Next Labs
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


from tergite_autocalibration.config.globals import CONFIG
from tergite_autocalibration.lib.nodes.qubit_control.motzoi_parameter.node import (
    MotzoiParameterNode,
)
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


def test_dummy_generation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = MotzoiParameterNode(CONFIG.run.qubits, CONFIG.run.couplers)
    dummy_dataset = node.generate_dummy_dataset()
    first_qubit = CONFIG.run.qubits[0]
    number_of_reps = len(node.schedule_samplespace["X_repetitions"][first_qubit])
    number_of_motzois = len(node.schedule_samplespace["mw_motzois"][first_qubit])

    assert len(dummy_dataset.data_vars) == len(CONFIG.run.qubits)
    assert dummy_dataset.data_vars[0].size == number_of_reps * number_of_motzois
