# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs AB 2024
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
from typing import Union, List, Iterator


def iter_module_files(
    module_folder: Union[str, Path],
    excluded_files: List[str] = None,
    file_types: List[str] = None,
) -> Iterator[Path]:
    """
    Generator that yields Python file paths, excluding specified files.

    Args:
        module_folder (Union[str, Path]): Path to the folder containing the Python modules
        excluded_files (List[str]): File names to exclude e.g. build files or certain modules
        file_types (List[str]): Which file types should be included, default: ".py" files only
    """

    if excluded_files is None:
        excluded_files = []

    if file_types is None:
        file_types = [".py"]

    # Iterate over all files in the module
    for dir_path, _, filenames in os.walk(module_folder):
        for filename in filenames:
            # Only take specified file types into account
            if any(filename.endswith(file_type) for file_type in file_types):
                file_path = os.path.join(dir_path, filename)

                # Exclude files containing substrings from the exclusion list
                if not any(substr in file_path for substr in excluded_files):
                    yield file_path
