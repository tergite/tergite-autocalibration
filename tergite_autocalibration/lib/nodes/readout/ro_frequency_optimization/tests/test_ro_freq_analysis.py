# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou  2026
# (C) Chalmers Next Labs AB 2026
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

from tergite_autocalibration.lib.base.utils.analysis_utils import filter_ds_by_element
from tergite_autocalibration.lib.nodes.readout.ro_frequency_optimization.analysis import (
    ROFrequencyThreeStateNodeAnalysis,
    ROFrequencyThreeStateQubitAnalysis,
)
from tergite_autocalibration.tests.utils.decorators import with_redis
from tergite_autocalibration.utils.io.dataset import open_dataset

_test_data_dir = os.path.join(
    Path(__file__).parent.parent.parent.parent, "data", "single_qubits_run"
)
_redis_values = os.path.join(_test_data_dir, "redis-single-qubits-run.json")


@with_redis(_redis_values)
def test_ro_freq_3states():
    name = "ro_frequency_three_state_optimization"
    qubit_qois = ["extended_clock_freqs:readout_3state_opt"]
    containing_path = os.path.join(_test_data_dir, name)
    full_dataset = open_dataset(name, containing_path)

    ds_13 = filter_ds_by_element(full_dataset, "q13")
    ds_15 = filter_ds_by_element(full_dataset, "q15")

    analysis = ROFrequencyThreeStateQubitAnalysis(name, qubit_qois)
    qoi_13 = analysis.process_qubit(ds_13)

    ro_frequency = qoi_13.analysis_result["extended_clock_freqs:readout_3state_opt"][
        "value"
    ]

    assert qoi_13.analysis_successful
    assert pytest.approx(ro_frequency) == 7181088888.888889

    qoi_15 = analysis.process_qubit(ds_15)

    ro_frequency = qoi_15.analysis_result["extended_clock_freqs:readout_3state_opt"][
        "value"
    ]

    assert qoi_15.analysis_successful
    assert pytest.approx(ro_frequency) == 7128822222.222222


@with_redis(_redis_values)
def test_plotting():
    """
    Test that the plotter produces a figure with the right number of axes
    """
    name = "ro_frequency_three_state_optimization"
    qubit_qois = ["extended_clock_freqs:readout_3state_opt"]
    containing_path = os.path.join(_test_data_dir, name)

    dataset = open_dataset(name, containing_path)

    analysis = ROFrequencyThreeStateNodeAnalysis(name, qubit_qois)
    analysis.analyze_node(dataset)
    number_of_qubits = len(analysis.dataset.attrs["elements"])
    assert analysis.axs.shape == (1, number_of_qubits)
