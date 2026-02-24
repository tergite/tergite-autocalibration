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

from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.measurement import (
    TwoQubitRBMeasurement,
)
from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.node import (
    CZ_RB_Node,
)
from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.utils.two_qubit_clifford_group import (
    TwoQubitClifford,
)
from tergite_autocalibration.tests.utils.decorators import with_redis
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon

_test_data_dir = os.path.join(Path(__file__).parent, "data")
_redis_values_path = os.path.join(_test_data_dir, "redis-2026-02-10-11-23-12.json")


@with_redis(_redis_values_path)
def test_align_cliffords():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    qubits = ["q13", "q14"]
    couplers = ["q13_q14"]
    clifford_gate_index = 9799

    node = CZ_RB_Node(all_qubits=qubits, couplers=couplers)
    transmons_dict = {qubit: node.device.get_element(qubit) for qubit in qubits}
    edges_dict = {coupler: node.device.get_edge(coupler) for coupler in couplers}
    cz_rb_measurement = TwoQubitRBMeasurement(
        transmons=transmons_dict, couplers=edges_dict
    )

    cliff_gate_decomposition = TwoQubitClifford(clifford_gate_index).gate_decomposition

    assert cliff_gate_decomposition == [
        ("mY90", "q0"),
        ("X90", "q0"),
        ("I", "q1"),
        ("CZ", ["q0", "q1"]),
        ("Y90", "q0"),
        ("mY90", "q1"),
        ("CZ", ["q0", "q1"]),
        ("mX90", "q0"),
        ("Y180", "q0"),
        ("mY90", "q1"),
    ]

    grouped_gate_decomposition = cz_rb_measurement.align_cliffords(
        couplers[0], cliff_gate_decomposition
    )

    assert grouped_gate_decomposition == [
        {"q0": ["mY90", "X90"], "q1": ["I", "I"]},
        {"q13_q14": ["CZ"]},
        {"q0": ["Y90"], "q1": ["mY90"]},
        {"q13_q14": ["CZ"]},
        {"q0": ["mX90", "Y180"], "q1": ["I", "mY90"]},
    ]
