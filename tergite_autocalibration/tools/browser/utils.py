# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2025
# (C) Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import os
from datetime import datetime
from pathlib import Path


def folders_containing_pngs(inter_path: Path) -> list:
    """
    Given an intermediate folder (calibration chain folder)
    scan whether the inner folders (folders of node measurements) contain png images
    """
    inner_folders = []
    for inner in os.listdir(inter_path):
        inner_path = os.path.join(inter_path, inner)
        if os.path.isdir(inner_path) and any(
            f.endswith(".png") for f in os.listdir(inner_path)
        ):
            try:
                inner_folders.append(
                    (
                        # the datetime helps to later sort the folder list
                        datetime.strptime(inner.split("_")[0][:15], "%Y%m%d-%H%M%S"),
                        inner,
                    )
                )
            except ValueError:
                continue
    inner_folders.sort(reverse=True, key=lambda x: x[0])
    valid_inners = [inner for _, inner in inner_folders]
    return valid_inners


def date_data_folders(data_directory: Path):
    """
    Given the DATA_DIR collect all the date folders matching the "%Y-%m-%d" format
    """
    date_folders = []
    for outer in os.listdir(data_directory):
        outer_path = os.path.join(data_directory, outer)
        if os.path.isdir(outer_path):
            try:
                # the datetime helps to later sort the folder list
                date_folders.append((datetime.strptime(outer, "%Y-%m-%d"), outer))
            except ValueError:
                continue

    date_folders.sort(reverse=True, key=lambda x: x[0])

    return date_folders


def collect_valid_chains(outer_path) -> dict:
    """
    A valid chain is a folder that contains (measurement) folders
    each having at least one png image
    """
    valid_intermediates = {}
    for inter in os.listdir(outer_path):
        inter_path = Path(os.path.join(outer_path, inter))
        if os.path.isdir(inter_path):
            valid_inners = folders_containing_pngs(inter_path)
            if valid_inners:
                valid_intermediates[inter] = valid_inners

    return valid_intermediates


# Scan and store folder structure
def scan_folders(data_directory: Path) -> dict[str, dict]:
    """
    scan the whole data directory for valid measurements, i.e.
    measurements that have produced png images
    """
    folder_data = {}
    outer_folders = date_data_folders(data_directory)

    for _, outer in outer_folders:

        outer_path = os.path.join(data_directory, outer)
        valid_intermediates = collect_valid_chains(outer_path)

        if valid_intermediates:
            sorted_valid_intermediates = {
                key: valid_intermediates[key] for key in sorted(valid_intermediates)
            }
            folder_data[outer] = sorted_valid_intermediates

    return folder_data
