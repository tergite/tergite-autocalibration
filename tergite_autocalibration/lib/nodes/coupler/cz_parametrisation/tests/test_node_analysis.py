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
import xarray as xr
from numpy import ndarray

from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.analysis import (
    CZParametrizationFixDurationNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.utils.no_valid_combination_exception import (
    NoValidCombinationException,
)


@pytest.fixture(autouse=True)
def setup_data_mutliple_files():
    # It should be a single dataset, but we do not have one yet, so we loop over existing files
    dataset_path = Path(__file__).parent / "data"  # / "dataset_fix_time_0.hdf5"
    node_analysis = CZParametrizationFixDurationNodeAnalysis("name", ["redis_field"])
    return node_analysis


def test_InitSetDataMember(
    setup_data_mutliple_files: CZParametrizationFixDurationNodeAnalysis,
):
    node_analysis = setup_data_mutliple_files

    assert node_analysis.name == "name"
    assert node_analysis.redis_fields == ["redis_field"]
