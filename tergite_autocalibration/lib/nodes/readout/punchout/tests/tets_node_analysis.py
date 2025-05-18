# This code is part of Tergite
#
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from pathlib import Path

import pytest

from tergite_autocalibration.lib.nodes.readout.punchout.analysis import (
    PunchoutNodeAnalysis,
)


@pytest.fixture(autouse=True)
def setup_data_mutliple_files():
    # It should be a single dataset, but we do not have one yet, so we loop over existing files
    node_analysis = PunchoutNodeAnalysis("name", ["redis_field"])
    return node_analysis


def test_InitSetDataMember(
    setup_data_mutliple_files: PunchoutNodeAnalysis,
):
    node_analysis = setup_data_mutliple_files

    assert node_analysis.name == "name"
    assert node_analysis.redis_fields == ["redis_field"]

