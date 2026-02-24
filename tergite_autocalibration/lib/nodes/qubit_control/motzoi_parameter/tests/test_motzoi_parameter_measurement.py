# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2025
# (C) Chalmers Next Labs AB 2025
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

from tergite_autocalibration.config.globals import CONFIG
from tergite_autocalibration.lib.nodes.qubit_control.motzoi_parameter.node import (
    MotzoiParameter12Node,
    MotzoiParameterNode,
)
from tergite_autocalibration.tests.utils.decorators import with_redis
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


_test_data_dir = os.path.join(
    Path(__file__).parent.parent.parent.parent, "data", "single_qubits_run"
)
_redis_values = os.path.join(_test_data_dir, "redis-single-qubits-run.json")


@with_redis(_redis_values)
def test_12_pulse_duration():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    qubits = ["q13", "q14", "q15"]
    node_12 = MotzoiParameter12Node(qubits, ["q13_q14"])
    samplespace = {  # small samplespace
        "mw_motzois": {qubit: np.linspace(-0.3, 0.3, 3) for qubit in qubits},
        "X_repetitions": {qubit: np.arange(1, 8, 4) for qubit in qubits},
    }
    transmons_dict = {qubit: node_12.device.get_element(qubit) for qubit in qubits}
    measurement_class = node_12.measurement_obj(transmons_dict)
    schedule = measurement_class.schedule_function(
        **samplespace, **node_12.schedule_keywords
    )
    for pulses in schedule.operations.values():
        if pulses["name"] == "DRAGPulse":
            pulse_duration = pulses["pulse_info"][0]["duration"]

    assert pytest.approx(pulse_duration) == 7.6e-8
