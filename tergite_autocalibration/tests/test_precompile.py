# This code is part of Tergite
#
# (C) Chalmers Next Labs AB 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import pytest

from tergite_autocalibration.lib.nodes.schedule_node import OuterScheduleNode
from tergite_autocalibration.lib.utils.node_factory import NodeFactory
from tergite_autocalibration.tests.utils.decorators import with_redis
from tergite_autocalibration.tests.utils.fixtures import get_fixture_path
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon
from tergite_autocalibration.utils.measurement_utils import (
    reduce_samplespace,
    samplespace_dimensions,
)

_redis_values = get_fixture_path("redis", "standard_redis_mock.json")
_node_factory = NodeFactory()
_node_names = _node_factory.all_node_names()


@pytest.mark.parametrize("node_name", _node_names)
@with_redis(_redis_values)
def test_precompile_all_nodes_without_error(node_name):
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = _node_factory.create_node(node_name, ["q00", "q01"], couplers=["q00_q01"])

    if node_name == "purity_benchmarking":
        pytest.skip(
            "We skip purity_benchmarking for now, because it needs some refactoring."
        )

    if issubclass(node.measurement_type, OuterScheduleNode):
        # The assembly of samplespaces is taken from the OuterScheduleNode
        outer_dimensions = samplespace_dimensions(node.outer_schedule_samplespace)
        iterations = outer_dimensions[0]
        for this_iteration in range(iterations):
            reduced_outer_samplespace = reduce_samplespace(
                this_iteration, node.outer_schedule_samplespace
            )
            samplespace = node.schedule_samplespace | reduced_outer_samplespace
            node.precompile(samplespace)

    else:
        node.precompile(node.schedule_samplespace)
