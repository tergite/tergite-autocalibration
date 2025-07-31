# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2025
# (C) Copyright Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from pathlib import Path

from tergite_autocalibration.tests.utils.fixtures import get_fixture_path
from tergite_autocalibration.tools.browser.utils import scan_folders

_DATADIR = Path(get_fixture_path("data", "browser"))


def test_folder_scan():
    folders = scan_folders(_DATADIR)
    date = "2025-07-23"
    good_chain = "12-47-07_ro_frequency_two_state_optimization-ACTIVE"

    # Check whether all measurement runs are fetched
    assert len(folders[date]) == 3

    # Check whether all measurements of a specific run are found
    measurements = folders[date][good_chain]
    assert len(measurements) == 13


# It is in fact not empty, because there is one file inside to commit the directory to git
_EMPTY_DATADIR = Path(get_fixture_path("data", "browser_empty"))


def test_empty_folder_scan():
    folders = scan_folders(_EMPTY_DATADIR)

    # Check whether it returns an empty dict
    assert isinstance(folders, dict)
    assert len(folders) == 0
