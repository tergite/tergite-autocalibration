# This code is part of Tergite
#
# (C) Copyright Stefan Hill 2024
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


def test_license_headers():
    # Find the path to the root directory of the package
    library_folder = (
        str(Path(__file__)).split("tergite_autocalibration")[0]
        + "tergite_autocalibration"
    )

    excluded_files = ["quantifiles"]

    # Iterate over all files in the whole package
    for dir_path, _, filenames in os.walk(library_folder):
        for filename in filenames:
            if filename.endswith(".py"):
                file_path = dir_path + "/" + filename

                # Check whether we should exclude the file based on its path e.g. some build files
                if any(substr_ in file_path for substr_ in excluded_files):
                    continue

                # Check whether the file has more than one line of code and contains a license header
                with open(file_path, "r", encoding="utf-8") as file:
                    lines = file.readlines()
                    line_count = len(lines)
                    if line_count > 0:
                        print(f"Check file: {file_path}")
                        assert lines[0].startswith("# This code is part of Tergite")
                    else:
                        print(f"Empty file: {file_path}")
