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
from tergite_autocalibration.utils.io.dataset import open_dataset

from tergite_autocalibration.lib.nodes.coupler.cz_local_phases.analysis import (
    CZLocalPhasesCouplerAnalysis,
)
from tergite_autocalibration.tests.utils.decorators import with_redis

_test_data_dir = os.path.join(Path(__file__).parent, "data")
_redis_values = os.path.join(_test_data_dir, "redis-coupler-run-2026-02.json")


@with_redis(_redis_values)
def test_cz_local_phases():
    name = "cz_local_phases"
    dataset = open_dataset(name, _test_data_dir)

    analysis = CZLocalPhasesCouplerAnalysis(
        name, ["cz_pulse_frequency", "cz_pulse_duration", "cz_phase"]
    )
    qoi = analysis.process_coupler(dataset, "q13_q14")

    control_local_phase = qoi.analysis_result["control_local_phase"]["value"]
    target_local_phase = qoi.analysis_result["target_local_phase"]["value"]

    assert qoi.analysis_successful
    assert pytest.approx(control_local_phase) == -135.2184
    assert pytest.approx(target_local_phase) == 73.0427


@with_redis(_redis_values)
def test_plotting():
    """
    Test that the plotter produces a figure with the right number of axes
    """
    name = "cz_local_phases"
    dataset = open_dataset(name, _test_data_dir)

    analysis = CZLocalPhasesCouplerAnalysis(
        name, ["cz_pulse_frequency", "cz_pulse_duration", "cz_phase"]
    )

    figures_dictionary = {}

    analysis.process_coupler(dataset, "q13_q14")
    analysis.plotter(figures_dictionary)

    assert "q13_q14" in figures_dictionary

    figure = figures_dictionary["q13_q14"][0]

    assert len(figure.get_axes()) == 4
