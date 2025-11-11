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
from tergite_autocalibration.lib.nodes.coupler.spectroscopy.node import (
    QubitSpectroscopyVsCurrentNode,
)
from tergite_autocalibration.lib.nodes.external_parameter_node import (
    ExternalParameterNode,
)
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


def test_measurement_01_type():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = QubitSpectroscopyVsCurrentNode("coupler_anticrossing", CONFIG.run.couplers)
    assert issubclass(node.measurement_type, ExternalParameterNode)


def test_dummy_generation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = QubitSpectroscopyVsCurrentNode("coupler_anticrossing", CONFIG.run.couplers)
    node.this_current = 0.0001
    dummy_dataset = node.generate_dummy_dataset()
    first_qubit = CONFIG.run.qubits[0]
    number_of_frequencies = len(
        node.schedule_samplespace["spec_frequencies"][first_qubit]
    )
    measured_qubits = [
        qubit for coupler in CONFIG.run.couplers for qubit in coupler.split("_")
    ]
    assert len(dummy_dataset.data_vars) == len(measured_qubits)
    assert dummy_dataset.data_vars[0].size == number_of_frequencies
