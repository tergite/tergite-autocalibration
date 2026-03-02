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
from tergite_autocalibration.lib.nodes.readout.ro_frequency_optimization.node import (
    ROFrequencyThreeStateOptimizationNode,
)
from tergite_autocalibration.tests.utils.decorators import with_redis
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


def test_dummy_generation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node_3 = ROFrequencyThreeStateOptimizationNode(
        CONFIG.run.qubits, CONFIG.run.couplers
    )
    dummy_dataset = node_3.generate_dummy_dataset()
    first_qubit = CONFIG.run.qubits[0]
    number_of_freqs = len(
        node_3.schedule_samplespace["ro_opt_frequencies"][first_qubit]
    )
    number_of_states = len(node_3.schedule_samplespace["qubit_states"][first_qubit])

    assert len(dummy_dataset.data_vars) == len(CONFIG.run.qubits)
    assert dummy_dataset.data_vars[0].size == number_of_freqs * number_of_states


_test_data_dir = os.path.join(
    Path(__file__).parent.parent.parent.parent, "data", "single-qubits-run"
)
_redis_values = os.path.join(_test_data_dir, "redis-single-qubits-run.json")


@pytest.mark.skip  # skiping due to dh legacy
@with_redis(_redis_values)
def test_12_pulse_duration():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    qubits = ["q13", "q14", "q15"]
    node_12 = ROFrequencyThreeStateOptimizationNode(qubits, ["q13_q14"])
    samplespace = {  # small samplespace
        "ro_opt_frequencies": {qubit: np.linspace(6.8e9, 6.9e9, 3) for qubit in qubits},
        "qubit_states": {qubit: np.array([0, 1, 2], dtype=np.int8) for qubit in qubits},
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
