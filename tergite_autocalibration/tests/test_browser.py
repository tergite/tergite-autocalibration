# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from pathlib import Path

import pytest


# from tergite_autocalibration.tests.utils.reflections import iter_module_files
from tergite_autocalibration.utils.logging import logger

# Find the path to the root directory of the package
# _library_folder = (
#     str(Path(__file__)).split("tergite_autocalibration")[0] + "tergite_autocalibration"
# )

from tergite_autocalibration.tools.plotly_browser.browser_utils import scan_folders
from tergite_autocalibration.tools.plotly_browser.dash_browser import app

from tergite_autocalibration.tests.utils.decorators import preserve_os_env, with_os_env
from tergite_autocalibration.tests.utils.fixtures import get_fixture_path
from dash.dependencies import MATCH

TEST_DATADIR = Path("tergite_autocalibration/tests/fixtures/data/browser/")

_DATA_DIR = get_fixture_path("data", "browser")


def test_folder_scan():
    folders = scan_folders(TEST_DATADIR)
    date = "2025-07-23"
    good_chain = "12-47-07_ro_frequency_two_state_optimization-ACTIVE"

    measurements = folders[date][good_chain]

    assert len(measurements) == 13
