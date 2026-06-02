# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2026
# (C) Chalmers Next Labs 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from tergite_autocalibration.lib.base.node import CouplerNode
from tergite_autocalibration.lib.nodes.coupler.zz_coupling.analysis import (
    ZZCouplingNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.zz_coupling.measurement import (
    ZZCouplingMeasurement,
)
from tergite_autocalibration.lib.nodes.coupler.zz_coupling.node import ZZCouplingNode
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


def test_node_creation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = ZZCouplingNode(all_qubits=["q13", "q14"], couplers=["q13_q14"])
    assert isinstance(node, CouplerNode)


def test_class_attribute_objects():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = ZZCouplingNode(all_qubits=["q13", "q14"], couplers=["q13_q14"])
    assert isinstance(node.measurement_obj, type(ZZCouplingMeasurement))
    assert isinstance(node.analysis_obj, type(ZZCouplingNodeAnalysis))
    assert issubclass(node.measurement_type, ScheduleNode)


def test_qubit_types():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = ZZCouplingNode(
        all_qubits=["q12", "q13", "q14", "q15"], couplers=["q12_q13", "q14_q15"]
    )

    qubit_types_dict = node.qubit_types()
    assert qubit_types_dict["q12_q13"]["active_qubit"] == "q12"
    assert qubit_types_dict["q12_q13"]["spectator_qubit"] == "q13"
    assert qubit_types_dict["q14_q15"]["active_qubit"] == "q14"
    assert qubit_types_dict["q14_q15"]["spectator_qubit"] == "q15"


def test_dummy_generation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated

    coupler = "q13_q14"
    couplers = [coupler]
    node = ZZCouplingNode(all_qubits=["q13", "q14"], couplers=couplers)
    dummy_dataset = node.generate_dummy_dataset()

    number_of_delays = len(node.schedule_samplespace["ramsey_delays"]["q13"])
    number_of_detunings = len(node.schedule_samplespace["artificial_detunings"]["q13"])
    number_of_spect_states = len(node.schedule_samplespace["spectator_states"][coupler])

    samples = number_of_delays * number_of_detunings * number_of_spect_states

    data_vars = dummy_dataset.data_vars

    assert len(data_vars) == 2 * len(couplers)
    assert data_vars[0].size == samples
