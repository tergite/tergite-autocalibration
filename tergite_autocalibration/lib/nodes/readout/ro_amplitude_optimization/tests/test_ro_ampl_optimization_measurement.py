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
from tergite_autocalibration.lib.nodes.readout.ro_amplitude_optimization.node import (
    ROAmplitudeThreeStateOptimizationNode,
)
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


def test_dummy_generation():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node_3 = ROAmplitudeThreeStateOptimizationNode(CONFIG.run.qubits, CONFIG.run.couplers
    )
    dummy_dataset = node_3.generate_dummy_dataset()
    first_qubit = CONFIG.run.qubits[0]
    number_of_ampls = len(node_3.schedule_samplespace["ro_amplitudes"][first_qubit])
    number_of_states = len(node_3.schedule_samplespace["qubit_states"][first_qubit])

    assert len(dummy_dataset.data_vars) == len(CONFIG.run.qubits)
    assert (
        dummy_dataset.data_vars[0].size
        == number_of_ampls * number_of_states * node_3.loops
    )
