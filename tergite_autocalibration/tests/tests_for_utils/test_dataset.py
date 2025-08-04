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

from tergite_autocalibration.tests.utils.fixtures import get_fixture_path
from tergite_autocalibration.utils.io.dataset import scrape_and_copy_hdf5_files


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
