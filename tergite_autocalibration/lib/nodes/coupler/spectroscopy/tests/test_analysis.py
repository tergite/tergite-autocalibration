# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2026
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
import shutil
from pathlib import Path

import pytest
import xarray as xr

from tergite_autocalibration.lib.nodes.coupler.spectroscopy.analysis import (
    CouplerSpectroscopyAnalysis,
)
from tergite_autocalibration.tests.utils.decorators import with_redis

_test_data_dir = os.path.join(Path(__file__).parent, "data")


def test_coupler_dc_spectroscopy_analysis():
    """
    Test whether single coupler analysis outputs right QOIs
    """
    # Load dataset
    file_path = os.path.join(_test_data_dir, "dataset_coupler_dc_spectroscopy.hdf5")
    dataset = xr.open_dataset(file_path)
    coupler = "q13_q14"
    coupler_qois = ["fmax", "Ic", "I0", "offset"]

    # Run the single coupler analysis
    analysis = CouplerSpectroscopyAnalysis("coupler_dc_spectroscopy", coupler_qois)
    qoi = analysis.process_coupler(dataset, coupler)

    # Compare the output values
    fmax = qoi.analysis_result["fmax"]["value"]
    Ic = qoi.analysis_result["Ic"]["value"]
    I0 = qoi.analysis_result["I0"]["value"]
    offset = qoi.analysis_result["offset"]["value"]
    assert pytest.approx(fmax) == 6611014068.078065
    assert pytest.approx(Ic) == 0.00033692673400593815
    assert pytest.approx(I0) == 0.0035229033127314496
    assert pytest.approx(offset) == 299999824.4245611


def test_plotting():
    """
    Test that the plotter produces a figure with the right number of axes
    """
    file_path = os.path.join(_test_data_dir, "dataset_coupler_dc_spectroscopy.hdf5")
    dataset = xr.open_dataset(file_path)

    coupler_qois = ["fmax", "Ic", "I0", "offset"]

    # Run the single coupler analysis
    analysis = CouplerSpectroscopyAnalysis("coupler_dc_spectroscopy", coupler_qois)

    figures_dictionary = {}

    analysis.process_coupler(dataset, "q13_q14")
    analysis.plotter(figures_dictionary)

    figure = figures_dictionary["q13_q14"][0]

    assert "q13_q14" in figures_dictionary
    assert len(figure.get_axes()) == 10  # 5 plots + 4 colorbars + 1 empty plot
