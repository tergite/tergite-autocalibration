# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Stefan Hill 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import pytest
import toml

from tergite_autocalibration.config import settings
from tergite_autocalibration.lib.utils.node_factory import NodeFactory
from tergite_autocalibration.tests.utils.env import setup_test_env

setup_test_env()


nodes = NodeFactory()
transmon_configuration = toml.load(settings.QOI_CONFIG)
# qois = transmon_configuration["qoi"]
# setup = mock.set_up_mock_transmon_setup()
# mock.set_standard_params_transmon(setup)


# FIXME: This test becomes redundant as soon as we are moving towards the new qoi structure, then we remove the skip
@pytest.mark.skip
def test_redis_loading():
    all_nodes = nodes.node_name_mapping.keys()
    for node in all_nodes:
        print(node)
        print(transmon_configuration)
        # assert node in qois["qubits"].keys() or node in qois["couplers"].keys()
