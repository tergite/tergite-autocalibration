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

import xarray as xr
import pytest

from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.analysis import (
    CZRBCouplerAnalysis,
)
from tergite_autocalibration.tests.utils.decorators import with_redis

_test_data_dir = os.path.join(Path(__file__).parent, "data")
_redis_values = os.path.join(_test_data_dir, "redis-2026-03-05-10-55-35.json")


@with_redis(_redis_values)
def test_cz_rb():
    file_path = os.path.join(_test_data_dir, "dataset_cz_rb.hdf5")
    dataset = xr.open_dataset(file_path)

    analysis = CZRBCouplerAnalysis("cz_rb", ["cz_fidelity"])
    qoi = analysis.process_coupler(dataset, "q12_q13")

    cz_fidelity = qoi.analysis_result["cz_fidelity"]["value"]

    assert qoi.analysis_successful
    assert pytest.approx(cz_fidelity) == 0.95848


@with_redis(_redis_values)
def test_plotting():
    """
    Test that the plotter produces a figure with the right number of axes
    """
    file_path = os.path.join(_test_data_dir, "dataset_cz_rb.hdf5")
    dataset = xr.open_dataset(file_path)

    analysis = CZRBCouplerAnalysis("cz_rb", ["cz_fidelity"])

    figures_dictionary = {}

    analysis.process_coupler(dataset, "q12_q13")
    analysis.plotter(figures_dictionary)

    assert "q12_q13" in figures_dictionary

    figure = figures_dictionary["q12_q13"][0]

    # one axis for the standard exponentials and one for the leakage RB exponentials
    assert len(figure.get_axes()) == 2
