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

import numpy as np
import pytest

from tergite_autocalibration.lib.nodes.characterization.randomized_benchmarking.measurement import (
    RandomizedBenchmarkingMeasurement,
)
from tergite_autocalibration.lib.nodes.characterization.randomized_benchmarking.node import (
    RandomizedBenchmarkingNode,
)
from tergite_autocalibration.tests.utils.decorators import with_redis
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon

_test_data_dir = os.path.join(Path(__file__).parent, "data")
_redis_values_path = os.path.join(_test_data_dir, "redis-2026-03-10-21-33-32.json")


@with_redis(_redis_values_path)
def test_align_cliffords():
    """
    Test whether the one_by_one or parallel schedule_keyword is
    correctly applied. Node that it would be safer to test compiled
    schedule durations, but this would require a mocj hardware config
    """

    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    qubits = ["q11", "q12", "q13", "q14", "q15"]
    couplers = ["q14_q15"]

    node = RandomizedBenchmarkingNode(all_qubits=qubits, couplers=couplers)
    transmons_dict = {qubit: node.device.get_element(qubit) for qubit in qubits}
    edges_dict = {coupler: node.device.get_edge(coupler) for coupler in couplers}
    measurement_class = RandomizedBenchmarkingMeasurement(transmons=transmons_dict)

    node.schedule_keywords["loop_repetitions"] = 2
    samplespace = {  # small samplespace
        "number_of_cliffords": {qubit: np.array([0, 8, 16]) for qubit in qubits},
    }
    outer_samplespace = {
        "seeds": {qubit: np.array([0]) for qubit in qubits},
        "interleave_gate": {qubit: np.array(["Standard"]) for qubit in qubits},
    }

    # Test parallel
    node.schedule_keywords["multiplexing"] = "parallel"
    schedule = measurement_class.schedule_function(
        **samplespace, **outer_samplespace, **node.schedule_keywords
    )

    for op_id, operation in schedule.data["operation_dict"].items():
        if operation["name"] == "LoopOperation":
            loop_id = op_id
            break
    shot = schedule.data["operation_dict"][loop_id]["control_flow_info"]["body"]

    for qubit in qubits:
        assert f"root_{qubit}" in shot.schedulables

    # Test one by one
    node.schedule_keywords["multiplexing"] = "one_by_one"
    schedule = measurement_class.schedule_function(
        **samplespace, **outer_samplespace, **node.schedule_keywords
    )

    for op_id, operation in schedule.data["operation_dict"].items():
        if operation["name"] == "LoopOperation":
            loop_id = op_id
            break
    shot = schedule.data["operation_dict"][loop_id]["control_flow_info"]["body"]

    for qubit in qubits:
        assert not f"root_{qubit}" in shot.schedulables
