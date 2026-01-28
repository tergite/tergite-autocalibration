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
from tergite_autocalibration.lib.nodes.qubit_control.ramsey_fringes.node import (
    RamseyFringes12Node,
    RamseyFringesNode,
)
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


def test_dummy_01_generation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = RamseyFringesNode(CONFIG.run.qubits)
    dummy_dataset_01 = node.generate_dummy_dataset()
    first_qubit = CONFIG.run.qubits[0]
    number_of_delays = len(node.schedule_samplespace["ramsey_delays"][first_qubit])
    number_of_detunings = len(
        node.schedule_samplespace["artificial_detunings"][first_qubit]
    )

    data_vars = dummy_dataset_01.data_vars
    assert len(data_vars) == len(CONFIG.run.qubits)
    assert data_vars[0].size == number_of_delays * number_of_detunings


def test_dummy_12_generation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = RamseyFringes12Node(CONFIG.run.qubits)
    dummy_dataset = node.generate_dummy_dataset()
    first_qubit = CONFIG.run.qubits[0]
    number_of_delays = len(node.schedule_samplespace["ramsey_delays"][first_qubit])
    number_of_detunings = len(
        node.schedule_samplespace["artificial_detunings"][first_qubit]
    )

    data_vars = dummy_dataset.data_vars
    assert len(data_vars) == len(CONFIG.run.qubits)
    assert data_vars[0].size == number_of_delays * number_of_detunings
