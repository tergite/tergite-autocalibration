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

from pathlib import Path

from tergite_autocalibration.tests.utils.reflections import iter_module_files
from tergite_autocalibration.utils.logging import logger

# Find the path to the root directory of the package
_library_folder = (
    str(Path(__file__)).split("tergite_autocalibration")[0] + "tergite_autocalibration"
)


def test_license_headers():
    excluded_files = ["quantifiles"]

    # Iterate over package files
    for file_path in iter_module_files(_library_folder, excluded_files):

        # Check whether the file has more than one line of code and contains a license header
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
            line_count = len(lines)

            if line_count > 0:
                logger.info(f"Check file: {file_path}")
                assert lines[0].startswith("# This code is part of Tergite")
            else:
                logger.info(f"Empty file: {file_path}")


def test_print_and_logging_statements():

    # Exclude the logging utils and this test file
    excluded_files = ["logging", "test_formatting"]

    # Iterate over package files
    for file_path in iter_module_files(_library_folder, excluded_files):

        # Check whether the file has more than one line of code and contains print or logging statements
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
            line_count = len(lines)

            if line_count > 0:
                logger.info(f"Check file: {file_path}")
                for line in lines:
                    # Check for print statements
                    assert "print(" not in line

                    # Check for all kind of logging statements
                    assert "logging.debug" not in line
                    assert "logging.info" not in line
                    assert "logging.warning" not in line
                    assert "logging.error" not in line
                    assert "logging.log" not in line
            else:
                logger.info(f"Empty file: {file_path}")
