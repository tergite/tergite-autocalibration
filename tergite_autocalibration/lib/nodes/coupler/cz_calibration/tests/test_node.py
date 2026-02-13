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
from tergite_autocalibration.lib.nodes.coupler.cz_calibration.analysis import (
    CZCalibrationNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_calibration.measurement import (
    CZ_CalibrationMeasurement,
)
from tergite_autocalibration.lib.nodes.coupler.cz_calibration.node import (
    CZ_CalibrationNode,
)
from tergite_autocalibration.lib.nodes.schedule_node import OuterScheduleNode
from tergite_autocalibration.tests.utils.decorators import with_redis
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon

_test_data_dir = os.path.join(Path(__file__).parent, "data")
_redis_values_path = os.path.join(_test_data_dir, "redis-2025-12-25-12-40-59.json")


@with_redis(_redis_values_path)
def test_node_creation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = CZ_CalibrationNode(all_qubits=["q13", "q14"], couplers=["q13_q14"])
    assert isinstance(node, CouplerNode)


@with_redis(_redis_values_path)
def test_class_attribute_objects():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = CZ_CalibrationNode(all_qubits=["q13", "q14"], couplers=["q13_q14"])
    assert isinstance(node.measurement_obj, type(CZ_CalibrationMeasurement))
    assert isinstance(node.analysis_obj, type(CZCalibrationNodeAnalysis))
    assert issubclass(node.measurement_type, OuterScheduleNode)


@with_redis(_redis_values_path)
def test_dummy_generation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated

    coupler = "q13_q14"
    couplers = [coupler]
    node = CZ_CalibrationNode(all_qubits=["q13", "q14"], couplers=couplers)
    dummy_dataset = node.generate_dummy_dataset()

    number_of_phases = len(node.schedule_samplespace["ramsey_phases"]["q13"])
    number_of_modes = len(node.schedule_samplespace["control_ons"][coupler])

    data_vars = dummy_dataset.data_vars

    assert len(data_vars) == 2 * len(couplers)
    assert data_vars[0].size == number_of_phases * number_of_modes * node.loops
