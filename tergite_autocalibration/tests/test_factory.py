# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from pathlib import Path

from tergite_autocalibration.lib.utils.node_factory import NodeFactory
from tergite_autocalibration.lib.utils.reflections import (
    find_inheriting_classes_ast_recursive,
)


def test_node_classes_exist():

    # This will create a factory
    node_factory = NodeFactory()

    # Then we load all node implementations that we can find across the node module
    nodes_path = Path(__file__).parent.parent / "lib" / "nodes"
    node_implementations_found = find_inheriting_classes_ast_recursive(nodes_path)

    # Now we iterate over all nodes that have a defined class in the node factory
    for node_name in node_factory.all_node_names():
        # Check whether the class was found previously when traversing the node module
        assert (
            node_factory.node_name_mapping[node_name]
            in node_implementations_found.keys()
        )
