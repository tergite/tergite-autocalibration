# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Tong Liu 2024
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import os.path
import shutil
from datetime import datetime
from pathlib import Path
from typing import Union
from uuid import uuid4

import numpy as np
import xarray

from tergite_autocalibration.config.globals import CONFIG
from tergite_autocalibration.utils.logging import logger


def to_real_dataset(iq_dataset: xarray.Dataset) -> xarray.Dataset:
    ds = iq_dataset.expand_dims("ReIm", axis=-1)  # Add ReIm axis at the end
    ds = xarray.concat([ds.real, ds.imag], dim="ReIm")
    return ds


def create_node_data_path(node_name: str) -> Path:
    """
    Create the folder where measurement results, plots and logs specific to the node are stored.

    Args:
        node_name: to create a data path for.

    Returns:
        Path to the measurement log folder as Path.

    """
    now_ = datetime.now()
    measurement_id = (
        f"{now_.strftime('%Y%m%d-%H%M%S-%f')[:19]}-{str(uuid4())[:6]}-{node_name}"
    )
    data_path = Path(os.path.join(CONFIG.run.log_dir, measurement_id))
    return data_path


def scrape_and_copy_hdf5_files(
    scrape_directory: Union[Path, str], target_directory: Union[Path, str]
):
    """
    Find all measurement result files and copy them to the target directory.

    Args:
        scrape_directory: Folder with measurement result files.
        target_directory: Target directory to copy files to.
    """

    # Find all data files
    directory = Path(scrape_directory)
    hdf5_files = list(directory.rglob("*.h5")) + list(directory.rglob("*.hdf5"))

    # Ensure the target directory exists
    os.makedirs(target_directory, exist_ok=True)

    # Iterate over files and copy to the new folder
    # Does not preserve any subfolder structures from the scrape directory
    for file in hdf5_files:
        destination_path = os.path.join(target_directory, file.name)
        shutil.copy2(file, destination_path)

    logger.info(f"Copied {len(hdf5_files)} files to {target_directory}.")


def save_dataset(
    result_dataset: xarray.Dataset, node_name: str, data_path: Path
) -> None:
    """
    Save the measurement dataset to a file.

    Args:
        result_dataset (xarray.Dataset): The dataset to save.
        node_name (str): Name of the node being measured.
        data_path (Path): Path where the dataset will be saved.
    """
    data_path.mkdir(parents=True, exist_ok=True)
    measurement_id = data_path.stem[0:19]

    result_dataset = result_dataset.assign_attrs(
        {"name": node_name, "tuid": measurement_id}
    )

    # to_netcdf doesn't like complex numbers, convert to real/imag to save:
    result_dataset_real = to_real_dataset(result_dataset)

    count = 0
    dataset_name = f"dataset_{node_name}_{count}.hdf5"
    while (data_path / dataset_name).is_file():
        count += 1
        dataset_name = f"dataset_{node_name}_{count}.hdf5"
    result_dataset_real.to_netcdf(data_path / dataset_name)


# TODO: how does this function work?
def tunneling_qubits(data_values: np.ndarray) -> np.ndarray:
    if data_values.shape[0] == 1:
        # Single-qubit demodulation
        data_values = data_values[0]
        dims = len(data_values.shape)
        # Transpose data_values
        return np.moveaxis(data_values, range(dims), range(dims - 1, -1, -1))
    else:
        dims = len(data_values.shape)
        # Transpose data_values.
        # The first dimension corresponds to the index of qubits.
        return np.moveaxis(data_values, range(1, dims), range(dims - 1, 0, -1))
