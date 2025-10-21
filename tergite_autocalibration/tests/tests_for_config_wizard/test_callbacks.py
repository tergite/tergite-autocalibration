# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2025
# (C) Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from tergite_autocalibration.tools.hardware_config_wizard.wizard import (
    connect_qubits_to_modules,
    update_module_numbers,
    update_static_inputs,
)


def test_update_static_inputs():
    layout = update_static_inputs(0, "q1", "cluster_1", "01", "ro", "cz")
    id = layout.children[0].children[1].id
    assert id["name"] == "cluster_1"


def test_update_module_numbers():
    # FIXME: this callback requires global storages. It should change to use dcc Stastes
    module_numbers = ["1-4"]
    id = [{"type": "cluster-input", "index": 0, "name": "cluster_1"}]
    layout = update_module_numbers(1, module_numbers, id)
    radio_box_container = layout.children[0].children[1]
    number_of_radio_boxes = len(
        radio_box_container.children
    )  # each child is a radio box
    assert number_of_radio_boxes == 4


def test_connect_qubits_to_modules():
    layout = connect_qubits_to_modules(1)
    # FIXME: this callback only uses global storages. It should change to use dcc Stastes
    pass


def test_capture_cluster_name():
    # FIXME: this callback only uses global storages. It should change to use dcc Stastes
    pass
    # id = [{"type": "cluster-input", "index": 0, "name": "cluster_1"}]
    # layout = capture_cluster_name("cluster_1", id)
