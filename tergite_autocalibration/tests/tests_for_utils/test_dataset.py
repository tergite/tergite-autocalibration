# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import os.path
import shutil
import pytest

from tergite_autocalibration.tests.utils.fixtures import get_fixture_path
from tergite_autocalibration.utils.io.dataset import scrape_and_copy_hdf5_files
import tergite_autocalibration.utils.reanalysis_utils as ra_utils
from datetime import datetime
from pathlib import Path


def test_scrape_and_copy_hdf5_files():
    """
    Base case, copies all measurement files and counts whether they are in the target directory
    """
    scrape_directory = os.path.join(
        get_fixture_path(),
        "data",
        "16-51-33_standard_run_ro_amplitude_three_state_optimization-SUCCESS",
    )
    target_directory = os.path.join(
        get_fixture_path(),
        "tmp",
        "16-51-33_standard_run_ro_amplitude_three_state_optimization-SUCCESS",
    )

    scrape_and_copy_hdf5_files(scrape_directory, target_directory)
    assert os.path.exists(target_directory)

    n_copied_files = os.listdir(target_directory)
    assert len(n_copied_files) == 15

    shutil.rmtree(target_directory)


def test_is_run_folder():
    """Check that the standard run test fixture is a run folder"""
    run_dir = os.path.join(
        get_fixture_path(),
        "data",
        "16-51-33_standard_run_ro_amplitude_three_state_optimization-SUCCESS",
    )
    assert ra_utils.is_run_folder(run_dir)


def test_is_measurement_folder():
    """Check that the standard run test fixture contains the correct measurement folders"""
    run_dir = Path(
        os.path.join(
            get_fixture_path(),
            "data",
            "16-51-33_standard_run_ro_amplitude_three_state_optimization-SUCCESS",
        )
    )
    measurement_folders = set(
        filter(lambda m: ra_utils.is_measurement_folder(m), run_dir.iterdir())
    )
    assert len(measurement_folders) == 15
    measurement_folders = set(map(lambda m: m.name, measurement_folders))

    assert measurement_folders == {
        "20250728-165136-525-9c2f16-resonator_spectroscopy",
        "20250728-165142-378-6c2eaa-qubit_01_spectroscopy",
        "20250728-165219-145-8960cd-rabi_oscillations",
        "20250728-165237-029-8e7bcc-ramsey_correction",
        "20250728-165346-613-912106-motzoi_parameter",
        "20250728-165426-836-fc0537-n_rabi_oscillations",
        "20250728-165458-851-fa4816-resonator_spectroscopy_1",
        "20250728-165524-927-753fdf-qubit_12_spectroscopy",
        "20250728-165602-013-a5fc29-rabi_oscillations_12",
        "20250728-165620-147-1dfae4-ramsey_correction_12",
        "20250728-165730-657-d5eed8-motzoi_parameter_12",
        "20250728-165807-020-2a9930-n_rabi_oscillations_12",
        "20250728-165843-459-edbc8e-resonator_spectroscopy_2",
        "20250728-165910-014-f02261-ro_frequency_three_state_optimization",
        "20250728-170030-376-c25885-ro_amplitude_three_state_optimization",
    }


def test_select_measurement_for_analysis_error_handling():
    """Test that the error handling for the reanalysis utils is working"""
    with pytest.raises(FileNotFoundError, match=r"^'apple' is not a run folder.$"):
        ra_utils.select_measurement_for_analysis("apple")

    run_dir = Path(
        os.path.join(
            get_fixture_path(),
            "data",
            "16-51-33_standard_run_ro_amplitude_three_state_optimization-SUCCESS",
        )
    )

    with pytest.raises(
        FileNotFoundError,
        match=(r"^The node name 'apple' was specified, but the run folder[\s\S]+"),
    ):
        ra_utils.select_measurement_for_analysis(run_dir, node_name="apple")


def test_select_measurement_for_analysis_can_find_measurement():
    """Test that we can create the measurement info for one of the measurement folder fixtures"""
    run_dir = Path(
        os.path.join(
            get_fixture_path(),
            "data",
            "16-51-33_standard_run_ro_amplitude_three_state_optimization-SUCCESS",
        )
    )

    info = ra_utils.select_measurement_for_analysis(
        run_dir, node_name="ramsey_correction"
    )

    assert info.timestamp == datetime(2025, 7, 28, 16, 52, 37)
    assert info.tuid == "20250728-165237-029-8e7bcc"
    assert info.msmt_idx == 4
    assert info.node_name == "ramsey_correction"
    assert info.measurement_folder_path == run_dir / f"{info.tuid}-{info.node_name}"
    assert info.run_folder_path == run_dir
    assert (
        info.dataset_path
        == info.measurement_folder_path / "dataset_ramsey_correction_0.hdf5"
    )
