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
from tergite_autocalibration.lib.nodes.qubit_control.rabi_oscillations.node import (
    NRabiOscillationsNode,
    RabiOscillations12Node,
    RabiOscillationsNode,
)
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


def test_dummy_01_generation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node_01 = RabiOscillationsNode(
        CONFIG.run.qubits, CONFIG.run.couplers
    )
    dummy_dataset_01 = node_01.generate_dummy_dataset()
    first_qubit = CONFIG.run.qubits[0]
    number_of_amplitudes_01 = len(
        node_01.schedule_samplespace["mw_amplitudes"][first_qubit]
    )

    assert len(dummy_dataset_01.data_vars) == len(CONFIG.run.qubits)
    assert dummy_dataset_01.data_vars[0].size == number_of_amplitudes_01


def test_dummy_12_generation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node_12 = RabiOscillations12Node(
        CONFIG.run.qubits, CONFIG.run.couplers
    )
    dummy_dataset_12 = node_12.generate_dummy_dataset()
    first_qubit = CONFIG.run.qubits[0]
    number_of_amplitudes_12 = len(
        node_12.schedule_samplespace["mw_amplitudes"][first_qubit]
    )

    assert len(dummy_dataset_12.data_vars) == len(CONFIG.run.qubits)
    assert dummy_dataset_12.data_vars[0].size == number_of_amplitudes_12


def test_dummy_n_rabi_generation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node_n_rabi = NRabiOscillationsNode(
        CONFIG.run.qubits, CONFIG.run.couplers
    )
    dummy_dataset_n_rabi = node_n_rabi.generate_dummy_dataset()
    first_qubit = CONFIG.run.qubits[0]
    number_of_reps = len(node_n_rabi.schedule_samplespace["X_repetitions"][first_qubit])
    number_of_amplitudes_n_rabi = len(
        node_n_rabi.schedule_samplespace["mw_amplitudes_sweep"][first_qubit]
    )

    assert len(dummy_dataset_n_rabi.data_vars) == len(CONFIG.run.qubits)
    assert (
        dummy_dataset_n_rabi.data_vars[0].size
        == number_of_reps * number_of_amplitudes_n_rabi
    )
