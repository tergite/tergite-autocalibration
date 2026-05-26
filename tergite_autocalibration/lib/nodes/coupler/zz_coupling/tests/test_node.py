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

import os
from pathlib import Path

from tergite_autocalibration.lib.base.node import CouplerNode
from tergite_autocalibration.lib.nodes.coupler.zz_coupling.analysis import (
    ZZCouplingNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.zz_coupling.measurement import (
    ZZCouplingMeasurement,
)
from tergite_autocalibration.lib.nodes.coupler.zz_coupling.node import ZZCouplingNode
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode
from tergite_autocalibration.tests.utils.decorators import with_redis
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon

# _test_data_dir = os.path.join(Path(__file__).parent, "data")
# _redis_values_path = os.path.join(_test_data_dir, "redis-2026-02-06-18.json")


@with_redis(_redis_values_path)
def test_node_creation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = ZZCouplingNode(all_qubits=["q13", "q14"], couplers=["q13_q14"])
    assert isinstance(node, CouplerNode)


@with_redis(_redis_values_path)
def test_class_attribute_objects():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = ZZCouplingNode(all_qubits=["q13", "q14"], couplers=["q13_q14"])
    assert isinstance(node.measurement_obj, type(ZZCouplingMeasurement))
    assert isinstance(node.analysis_obj, type(ZZCouplingNodeAnalysis))
    assert issubclass(node.measurement_type, ScheduleNode)


@with_redis(_redis_values_path)
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
    assert data_vars[0].size == samples * node.loops
