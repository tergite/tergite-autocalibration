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
from tergite_autocalibration.lib.nodes.readout.resonator_spectroscopy.node import (
    ResonatorSpectroscopy1Node,
    ResonatorSpectroscopy2Node,
    ResonatorSpectroscopyNode,
)
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


def test_measurement_0_type():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node_0 = ResonatorSpectroscopyNode("resonator_spectroscopy", CONFIG.run.qubits , CONFIG.run.couplers)
    assert issubclass(node_0.measurement_type, ScheduleNode)


def test_measurement_1_type():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node_1 = ResonatorSpectroscopy1Node("resonator_spectroscopy_1", CONFIG.run.qubits , CONFIG.run.couplers)
    assert issubclass(node_1.measurement_type, ScheduleNode)


def test_measurement_2_type():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node_2 = ResonatorSpectroscopy2Node("resonator_spectroscopy_2", CONFIG.run.qubits , CONFIG.run.couplers)
    assert issubclass(node_2.measurement_type, ScheduleNode)


def test_dummy_0_generation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = ResonatorSpectroscopyNode("resonator_spectroscopy", CONFIG.run.qubits , CONFIG.run.couplers)
    dummy_dataset_0 = node.generate_dummy_dataset()
    first_qubit = CONFIG.run.qubits[0]
    number_of_frequencies = len(
        node.schedule_samplespace["ro_frequencies"][first_qubit]
    )
    assert len(dummy_dataset_0.data_vars) == len(CONFIG.run.qubits)
    assert dummy_dataset_0.data_vars[0].size == number_of_frequencies


def test_dummy_1_generation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = ResonatorSpectroscopy1Node("resonator_spectroscopy_1", CONFIG.run.qubits , CONFIG.run.couplers)
    dummy_dataset_1 = node.generate_dummy_dataset()
    first_qubit = CONFIG.run.qubits[0]
    number_of_frequencies = len(
        node.schedule_samplespace["ro_frequencies"][first_qubit]
    )
    assert len(dummy_dataset_1.data_vars) == len(CONFIG.run.qubits)
    assert dummy_dataset_1.data_vars[0].size == number_of_frequencies


def test_dummy_2_generation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = ResonatorSpectroscopy2Node("resonator_spectroscopy_2", CONFIG.run.qubits , CONFIG.run.couplers)
    dummy_dataset_2 = node.generate_dummy_dataset()
    first_qubit = CONFIG.run.qubits[0]
    number_of_frequencies = len(
        node.schedule_samplespace["ro_frequencies"][first_qubit]
    )
    assert len(dummy_dataset_2.data_vars) == len(CONFIG.run.qubits)
    assert dummy_dataset_2.data_vars[0].size == number_of_frequencies
