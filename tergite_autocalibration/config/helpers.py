# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from pathlib import Path
from typing import Union


def save_configuration_snapshot(filepath: Union[str, Path], zip_file: bool = True):
    """
    Store the whole configuration package as a snapshot.
    This includes all configuration files as specified in the .env files and even the .env file itself

    Args:
        filepath: Path to where the configuration should be stored
        zip_file: Whether it should be put into a zip folder

    Returns:

    """


def load_configuration_snapshot(filepath: Union[str, Path]):
    """
    Load configuration files from a specified path.

    Args:
        filepath: Path to load from, can be a folder or a zipfile

    Returns:

    """
    pass
