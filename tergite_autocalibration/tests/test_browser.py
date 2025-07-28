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
# from tergite_autocalibration.utils.logging import logger

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


@with_os_env({"DATA_DIR": _DATA_DIR})
def test_image_display(dash_duo):
    outer = TEST_DATADIR / "2025-07-23"
    inter = outer / "12-47-07_ro_frequency_two_state_optimization-ACTIVE"
    inner = inter / "20250723-122627-108-80c1f0-resonator_spectroscopy"

    dash_duo.start_server(app)

    index = ""  # adjust if using "A"/"B" for Compare mode

    # Get all dropdown components (they have class name 'Select-control' in Dash)
    dropdowns = dash_duo.find_elements("div.Select-control")

    print("*" * 100)
    print("\nFound dropdowns:")
    for i, dropdown in enumerate(dropdowns):
        print(f"Dropdown {i}: {dropdown.text}")

    assert len(dropdowns) == 0

    # Select outer folder
    # dash_duo.select_dcc_dropdown(
    #     f'{{"type":"outer-selector","index":"{index}"}}', outer
    # )

    # dash_duo.wait_for_text_to_equal(
    #     f'{{"type":"intermediate-selector","index":"{index}"}} label', inter, timeout=3
    # )
    #
    # dash_duo.select_dcc_dropdown(
    #     f'{{"type":"intermediate-selector","index":"{index}"}}', inter
    # )
    #
    # dash_duo.wait_for_text_to_equal(
    #     f'{{"type":"inner-selector","index":"{index}"}} label', inner, timeout=3
    # )
    #
    # dash_duo.select_dcc_dropdown(
    #     f'{{"type":"inner-selector","index":"{index}"}}', inner
    # )
    #
    # # Wait for image to load in image tab
    # dash_duo.wait_for_element(
    #     f'{{"type":"tab-content","index":"{index}"}} img', timeout=5
    # )
    #
    # # Optional: Assert something about the image or its src
    # image = dash_duo.find_element(f'{{"type":"tab-content","index":"{index}"}} img')
    # assert "data:image/png;base64" in image.get_attribute("src")
