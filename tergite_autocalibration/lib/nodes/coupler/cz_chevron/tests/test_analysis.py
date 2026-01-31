# This code is part of Tergite
#
# (C) Copyright Michele Eleftherios Moschandreou  2026
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
import xarray as xr

from tergite_autocalibration.lib.nodes.coupler.cz_chevron.analysis import (
    CZChevronCouplerAnalysis,
)
from tergite_autocalibration.tests.utils.decorators import with_redis

_test_data_dir = os.path.join(Path(__file__).parent, "data")
_redis_values_0 = os.path.join(_test_data_dir, "data_0", "redis-export-2025-12-21.json")


@with_redis(_redis_values_0)
def test_cz_chevron_analysis_good_data():
    """
    Test whether single coupler analysis outputs right QOIs
    """
    # Load dataset
    file_path = os.path.join(_test_data_dir, "data_0", "dataset_cz_chevron_0.hdf5")
    dataset = xr.open_dataset(file_path)
    number_of_working_points = 3

    # Run the single coupler analysis
    analysis = CZChevronCouplerAnalysis(
        "cz_chevron",
        ["cz_working_frequencies", "cz_working_durations_in_ns"],
        phase_path="via_20",
        number_of_working_points=number_of_working_points,
    )
    qoi = analysis.process_coupler(dataset, "q13_q14")
    cz_working_frequencies = eval(
        qoi.analysis_result["cz_working_frequencies"]["value"]
    )
    cz_working_durations_in_ns = eval(
        qoi.analysis_result["cz_working_durations_in_ns"]["value"]
    )

    assert qoi.analysis_successful
    assert len(cz_working_frequencies) == number_of_working_points
    assert len(cz_working_durations_in_ns) == number_of_working_points
    assert 715415456 in cz_working_frequencies
    assert 408 in cz_working_durations_in_ns


@with_redis(_redis_values_0)
@pytest.mark.skip
def test_cz_chevron_analysis_bad_data():
    """
    Test whether single coupler analysis outputs that the analysis fails on bad data
    """
    # Load dataset
    file_path = os.path.join(_test_data_dir, "data_1", "dataset_cz_chevron_0.hdf5")
    dataset = xr.open_dataset(file_path)

    # Run the single coupler analysis
    analysis = CZChevronCouplerAnalysis(
        "cz_chevron",
        ["cz_pulse_frequency", "cz_pulse_amplitude", "parking_current"],
        phase_path="via_20",
    )
    qoi = analysis.process_coupler(dataset, "q14_q15")

    # Make sure that the analysis returns as unsuccessful
    assert qoi.analysis_successful is False


@with_redis(_redis_values_0)
def test_plotting(tmp_path):
    """
    Test whether plotting produces right plots
    """

    # Load dataset
    file_path = os.path.join(_test_data_dir, "data_0", "dataset_cz_chevron_0.hdf5")
    dataset = xr.open_dataset(file_path)
    number_of_working_points = 3
    figures_dictionary = {}

    # Run the single coupler analysis
    analysis = CZChevronCouplerAnalysis(
        "cz_chevron",
        ["cz_working_frequencies", "cz_working_durations_in_ns"],
        phase_path="via_20",
        number_of_working_points=number_of_working_points,
    )
    analysis.process_coupler(dataset, "q13_q14")
    analysis.plotter(figures_dictionary)

    assert "q13_q14" in figures_dictionary

    faceted_graph_fig = figures_dictionary["q13_q14"][0]

    # the faceted graph has 7 axis: 6 for the probabilty heatmaps and one for the colorbar
    assert len(faceted_graph_fig.get_axes()) == 7
