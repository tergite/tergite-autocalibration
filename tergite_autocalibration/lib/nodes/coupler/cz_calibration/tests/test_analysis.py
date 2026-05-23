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

import cf_xarray as cf
import pytest

from tergite_autocalibration.lib.nodes.coupler.cz_calibration.analysis import (
    CZCalibrationCouplerAnalysis,
)
from tergite_autocalibration.tests.utils.decorators import with_redis
from tergite_autocalibration.utils.io.dataset import open_dataset

_test_data_dir = Path(os.path.join(Path(__file__).parent, "data"))
_redis_values = os.path.join(_test_data_dir, "redis-coupler-run-2026-02.json")


@with_redis(_redis_values)
def test_cz_calibration_success():
    name = "cz_calibration"
    dataset = open_dataset(name, _test_data_dir)

    analysis = CZCalibrationCouplerAnalysis(
        "cz_calibration",
        ["cz_pulse_frequency", "cz_pulse_duration", "cz_phase"],
    )
    qoi = analysis.process_coupler(dataset, "q13_q14")

    cz_pulse_frequency = qoi.analysis_result["cz_pulse_frequency"]["value"]
    cz_pulse_duration = qoi.analysis_result["cz_pulse_duration"]["value"]
    cz_phase = qoi.analysis_result["cz_phase"]["value"]

    assert qoi.analysis_successful
    assert pytest.approx(cz_pulse_frequency) == 713980000
    assert pytest.approx(cz_pulse_duration) == 192e-9
    assert pytest.approx(cz_phase) == 181.450086


@with_redis(_redis_values)
def test_decode_multi_index():
    name = "cz_calibration"
    dataset = open_dataset(name, _test_data_dir)

    assert "l1" in dataset.working_points.coords
    assert "l2" in dataset.working_points.coords
    assert "working_points" in dataset.working_points.coords
    assert dataset.working_points.size == 11


@with_redis(_redis_values)
def test_plotting():
    """
    Test that the plotter produces a figure with the right number of axes
    """
    name = "cz_calibration"
    dataset = open_dataset(name, _test_data_dir)

    analysis = CZCalibrationCouplerAnalysis(
        "cz_calibration",
        ["cz_pulse_frequency", "cz_pulse_duration", "cz_phase"],
    )

    figures_dictionary = {}

    analysis.process_coupler(dataset, "q13_q14")
    analysis.plotter(figures_dictionary)

    assert "q13_q14" in figures_dictionary

    figure = figures_dictionary["q13_q14"][0]

    # axes are the (freq, duration) plots + figure title +
    # figure x label + figure y label + global trend plot
    assert len(figure.get_axes()) == dataset.working_points.size + 4
