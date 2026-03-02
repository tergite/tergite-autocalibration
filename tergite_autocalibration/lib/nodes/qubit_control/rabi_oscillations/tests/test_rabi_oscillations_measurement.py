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
from tergite_autocalibration.lib.nodes.qubit_control.rabi_oscillations.node import (
    NRabiOscillations12Node,
    NRabiOscillationsNode,
    RabiOscillations12Node,
    RabiOscillationsNode,
)
from tergite_autocalibration.tests.utils.decorators import with_redis
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


def test_dummy_01_generation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node_01 = RabiOscillationsNode(CONFIG.run.qubits, CONFIG.run.couplers)
    dummy_dataset_01 = node_01.generate_dummy_dataset()
    first_qubit = CONFIG.run.qubits[0]
    number_of_amplitudes_01 = len(
        node_01.schedule_samplespace["mw_amplitudes"][first_qubit]
    )

    assert len(dummy_dataset_01.data_vars) == len(CONFIG.run.qubits)
    assert dummy_dataset_01.data_vars[0].size == number_of_amplitudes_01


def test_dummy_12_generation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node_12 = RabiOscillations12Node(CONFIG.run.qubits, CONFIG.run.couplers)
    dummy_dataset_12 = node_12.generate_dummy_dataset()
    first_qubit = CONFIG.run.qubits[0]
    number_of_amplitudes_12 = len(
        node_12.schedule_samplespace["mw_amplitudes"][first_qubit]
    )

    assert len(dummy_dataset_12.data_vars) == len(CONFIG.run.qubits)
    assert dummy_dataset_12.data_vars[0].size == number_of_amplitudes_12


_test_data_dir = os.path.join(
    Path(__file__).parent.parent.parent.parent, "data", "single_qubits_run"
)
_redis_values = os.path.join(_test_data_dir, "redis-single-qubits-run.json")


@with_redis(_redis_values)
def test_12_pulse_duration():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    qubits = ["q13", "q14", "q15"]
    node_12 = RabiOscillations12Node(qubits, ["q13_q14"])
    samplespace = {  # small samplespace
        "mw_amplitudes": {qubit: np.linspace(0.002, 0.800, 3) for qubit in qubits}
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


def test_dummy_n_rabi_generation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node_n_rabi = NRabiOscillationsNode(CONFIG.run.qubits, CONFIG.run.couplers)
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


@with_redis(_redis_values)
def test_12_pulse_duration():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    qubits = ["q13", "q14", "q15"]
    node_12 = NRabiOscillations12Node(qubits, ["q13_q14"])
    samplespace = {
        "mw_amplitudes_sweep": {qubit: np.linspace(-0.05, 0.05, 3) for qubit in qubits},
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
