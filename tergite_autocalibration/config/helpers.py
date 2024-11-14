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

import os
import shutil
from pathlib import Path
from typing import Union

from tergite_autocalibration.config.settings import (
    RUN_CONFIG,
    CLUSTER_CONFIG,
    SPI_CONFIG,
    DEVICE_CONFIG,
    NODE_CONFIG,
    USER_SAMPLESPACE,
    ROOT_DIR,
)


def save_configuration_snapshot(
    filepath: Union[str, Path], zip_file: bool = True, save_env: bool = True
):
    """
    Store the whole configuration package as a snapshot.
    This includes all configuration files as specified in the .env files and even the .env file itself

    Args:
        filepath: Path to where the configuration should be stored
        zip_file: Whether it should be put into a zip folder
        save_env: Whether the environmental variables should be saved as well

    Returns:

    """

    # Create the output directory
    if not os.path.isabs(filepath):
        filepath = os.path.abspath(filepath)
    os.makedirs(filepath, exist_ok=True)

    configuration_files = [
        RUN_CONFIG,
        CLUSTER_CONFIG,
        SPI_CONFIG,
        DEVICE_CONFIG,
        NODE_CONFIG,
        USER_SAMPLESPACE,
    ]

    # Iterate over all configuration files and copy them to the destination
    for configuration_file in configuration_files:
        filename = os.path.basename(configuration_file)
        shutil.copy(configuration_file, os.path.join(filepath, filename))

    # If the .env file should be saved as well, copy it to the destination
    if save_env:
        shutil.copy(os.path.join(ROOT_DIR, ".env"), os.path.join(filepath, ".env"))

    if zip_file:
        shutil.make_archive(filepath, "zip", root_dir=filepath)
        shutil.rmtree(filepath)


def load_configuration_snapshot(filepath: Union[str, Path]):
    """
    Load configuration files from a specified path.

    Args:
        filepath: Path to load from, can be a folder or a zipfile

    Returns:

    """
    raise NotImplementedError(
        "Loading configuration snapshots is not implemented for now."
    )
