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

from tergite_autocalibration.config.globals import DATA_DIR


# Scan and store folder structure
def scan_folders():
    folder_data = {}
    outer_folders = []

    for outer in os.listdir(DATA_DIR):
        outer_path = os.path.join(DATA_DIR, outer)
        if os.path.isdir(outer_path):
            try:
                outer_folders.append((datetime.strptime(outer, "%Y-%m-%d"), outer))
            except ValueError:
                continue

    outer_folders.sort(reverse=True, key=lambda x: x[0])

    for _, outer in outer_folders:
        outer_path = os.path.join(DATA_DIR, outer)
        valid_intermediates = {}
        for inter in os.listdir(outer_path):
            inter_path = os.path.join(outer_path, inter)
            if os.path.isdir(inter_path):
                inner_folders = []
                for inner in os.listdir(inter_path):
                    inner_path = os.path.join(inter_path, inner)
                    if os.path.isdir(inner_path) and any(
                        f.endswith(".png") for f in os.listdir(inner_path)
                    ):
                        try:
                            inner_folders.append(
                                (
                                    datetime.strptime(
                                        inner.split("_")[0][:15], "%Y%m%d-%H%M%S"
                                    ),
                                    inner,
                                )
                            )
                        except ValueError:
                            continue
                inner_folders.sort(reverse=True, key=lambda x: x[0])
                valid_inners = [inner for _, inner in inner_folders]
                if valid_inners:
                    valid_intermediates[inter] = valid_inners
        if valid_intermediates:
            sorted_valid_intermediates = {
                key: valid_intermediates[key] for key in sorted(valid_intermediates)
            }
            folder_data[outer] = sorted_valid_intermediates

    return folder_data
