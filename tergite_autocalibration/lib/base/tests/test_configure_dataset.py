# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


from tergite_autocalibration.config.globals import CONFIG
from tergite_autocalibration.lib.nodes.readout.resonator_spectroscopy.node import (
    ResonatorSpectroscopyNode,
)
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


def test_configure_dataset_qubits():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node_0 = ResonatorSpectroscopyNode("resonator_spectroscopy", CONFIG.run.qubits)

    raw_ds = node_0.generate_dummy_dataset()

    configured_ds =  node_0.configure_dataset(raw_ds)
    breakpoint()


# def test_dummy_0_generation():
#     ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
#     node = ResonatorSpectroscopyNode("resonator_spectroscopy", CONFIG.run.qubits)
#     dummy_dataset_0 = node.generate_dummy_dataset()
#     first_qubit = CONFIG.run.qubits[0]
#     number_of_frequencies = len(
#         node.schedule_samplespace["ro_frequencies"][first_qubit]
#     )
#     assert len(dummy_dataset_0.data_vars) == len(CONFIG.run.qubits)
#     assert dummy_dataset_0.data_vars[0].size == number_of_frequencies




