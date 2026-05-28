# This code is part of Tergite
#
# (C) Copyright Michele Faucci Giannelli 2024
# (C) Copyright Eleftherios Moschandreou 2025, 2026
# (C) Chalmers Next Labs AB 2025, 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import math
import os
import shutil
from pathlib import Path

from tergite_autocalibration.lib.nodes.coupler.cz_parametrization.analysis import (
    CZParametrizationCouplerAnalysis,
)
from tergite_autocalibration.tests.utils.decorators import with_redis
from tergite_autocalibration.utils.io.dataset import open_dataset, save_figures

_test_data_dir = Path(os.path.join(Path(__file__).parent, "data"))
_test_data_dir_0 = Path(os.path.join(_test_data_dir, "data_0"))
_test_data_dir_1 = Path(os.path.join(_test_data_dir, "data_1"))
_redis_values = Path(os.path.join(_test_data_dir, "redis-export-2025-12-16.json"))


@with_redis(_redis_values)
def test_cz_parametrization_analysis_good_data():
    """
    Test whether single coupler analysis outputs right QOIs
    """
    # Load dataset
    name = "cz_parametrization"
    dataset = open_dataset(name, _test_data_dir_0)
    coupler = "q14_q15"

    # Run the single coupler analysis
    analysis = CZParametrizationCouplerAnalysis(
        name,
        ["cz_pulse_frequency", "cz_pulse_amplitude", "parking_current"],
        phase_path="via_20",
    )
    qoi = analysis.process_coupler(dataset, coupler)

    # Compare the output values
    assert math.isclose(
        qoi.analysis_result["cz_pulse_frequency"]["value"], 415004736.84210527
    )
    assert math.isclose(
        qoi.analysis_result["cz_pulse_amplitude"]["value"], 0.28448275862068967
    )
    assert math.isclose(
        qoi.analysis_result["parking_current"]["value"], 0.0006400000000000002
    )


@with_redis(_redis_values)
def test_cz_parametrization_analysis_bad_data():
    """
    Test whether single coupler analysis outputs that the analysis fails on bad data
    """
    # Load dataset
    name = "cz_parametrization"
    dataset = open_dataset(name, _test_data_dir_1)
    coupler = "q14_q15"

    # Run the single coupler analysis
    analysis = CZParametrizationCouplerAnalysis(
        "cz_parametrization",
        ["cz_pulse_frequency", "cz_pulse_amplitude", "parking_current"],
        phase_path="via_20",
    )
    qoi = analysis.process_coupler(dataset, coupler)

    # Make sure that the analysis returns as unsuccessful
    assert qoi.analysis_successful is False


@with_redis(_redis_values)
def test_plotting(tmp_path):
    """
    Test whether plotting produces right plots
    """

    # Copy dataset to the temporary data path
    shutil.copy(
        os.path.join(_test_data_dir, "data_0", "dataset_cz_parametrization.hdf5"),
        os.path.join(tmp_path, "dataset_cz_parametrization.hdf5"),
    )

    coupler = "q14_q15"
    name = "cz_parametrization"
    dataset = open_dataset(name, _test_data_dir_0)
    # Run the node analysis
    analysis = CZParametrizationCouplerAnalysis(
        "cz_parametrization",
        ["cz_pulse_frequency", "cz_pulse_amplitude", "parking_current"],
        **{"phase_path": "via_20"},
    )

    figures_dictionary = {}

    analysis.process_coupler(dataset, "q14_q15")
    analysis.plotter(figures_dictionary)

    assert "q14_q15" in figures_dictionary

    figures_list = figures_dictionary["q14_q15"]
    save_figures(figures_list, name, tmp_path)

    # Check whether output images exist
    for i in range(5):
        assert os.path.exists(
            os.path.join(tmp_path, f"cz_parametrization_{i}_preview.png")
        )
