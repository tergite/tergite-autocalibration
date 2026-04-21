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

import pytest


from tergite_autocalibration.utils.io.dataset import open_dataset
from tergite_autocalibration.lib.base.utils.analysis_utils import filter_ds_by_element
from tergite_autocalibration.lib.nodes.characterization.randomized_benchmarking.analysis import (
    RandomizedBenchmarkingNodeAnalysis,
    RandomizedBenchmarkingQubitAnalysis,
)
from tergite_autocalibration.tests.utils.decorators import with_redis

_test_data_dir = os.path.join(Path(__file__).parent, "data")
_redis_values = os.path.join(_test_data_dir, "redis-2026-03-10-21-33-32.json")


@with_redis(_redis_values)
def test_randomized_benchmarking_analysis():
    name = "randomized_benchmarking"
    dataset = open_dataset(name, _test_data_dir)

    qubit_qois = ["fidelity", "fidelity_error", "leakage", "leakage_error"]
    analysis = RandomizedBenchmarkingQubitAnalysis(name, qubit_qois)
    ds_11 = filter_ds_by_element(dataset, "q11")
    ds_15 = filter_ds_by_element(dataset, "q15")
    qoi_11 = analysis.process_qubit(ds_11, "q11")
    qoi_15 = analysis.process_qubit(ds_15, "q15")

    standard_fidelity_11 = qoi_11.analysis_result["fidelity"]["value"]
    standard_leakage_11 = qoi_11.analysis_result["leakage"]["value"]
    standard_fidelity_15 = qoi_15.analysis_result["fidelity"]["value"]
    standard_leakage_15 = qoi_15.analysis_result["leakage"]["value"]

    assert qoi_11.analysis_successful
    assert qoi_15.analysis_successful
    assert pytest.approx(standard_fidelity_11) == 0.998669
    assert pytest.approx(standard_leakage_11) == 0.00207032
    assert pytest.approx(standard_fidelity_15) == 0.9962656
    assert pytest.approx(standard_leakage_15) == 0.0064318


@with_redis(_redis_values)
def test_plotting():
    """
    Test that the plotter produces a figure with the right number of axes
    """
    name = "randomized_benchmarking"
    file_path = os.path.join(_test_data_dir, "dataset_randomized_benchmarking.hdf5")
    dataset = open_dataset(name, _test_data_dir)

    qubit_qois = ["fidelity", "fidelity_error", "leakage", "leakage_error"]
    analysis = RandomizedBenchmarkingNodeAnalysis(name, qubit_qois)
    analysis.analyze_node(dataset)
    figure = analysis.fig
    # TODO: this will change when the top band is removed
    assert len(figure.get_axes()) == 8
