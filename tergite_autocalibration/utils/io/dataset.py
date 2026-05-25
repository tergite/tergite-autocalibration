# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Tong Liu 2024
# (C) Copyright Michele Faucci Giannelli 2024, 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import json
import os.path
import shutil
from datetime import datetime
from pathlib import Path
from typing import Union
from uuid import uuid4

import cf_xarray as cf
import xarray

from tergite_autocalibration.config.globals import CONFIG
from tergite_autocalibration.utils.dto.qoi import QOI
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


def open_dataset(name: str, containing_folder_path: Path) -> xarray.Dataset:
    """
    Open the dataset for the analysis.

    Returns:
        the complex xarray.Dataset with measurement results

    """
    dataset_name = f"dataset_{name}.hdf5"
    dataset_path = os.path.join(containing_folder_path, dataset_name)
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    logger.info("Open dataset " + str(dataset_path))
    real_ds = xarray.open_dataset(dataset_path)
    if "working_points" in real_ds.coords:
        real_ds = cf.decode_compress_to_multi_index(real_ds, "working_points")
    complex_ds = real_ds.isel(ReIm=0) + 1j * real_ds.isel(ReIm=1)
    for var in real_ds.data_vars:
        attrs = real_ds.data_vars[var].attrs
        complex_ds[var].attrs.update(**attrs)
    ds_attrs = real_ds.attrs
    complex_ds.attrs.update(**ds_attrs)
    return complex_ds


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
    measurement_id = data_path.stem[0:19]

    result_dataset = result_dataset.assign_attrs(
        {"name": node_name, "tuid": measurement_id}
    )

    # to_netcdf doesn't like complex numbers, convert to real&imag to save:
    result_dataset_real = to_real_dataset(result_dataset)

    dataset_name = f"dataset_{node_name}.hdf5"
    if "working_points" in result_dataset_real.coords:
        result_dataset_real = cf.encode_multi_index_as_compress(
            result_dataset_real, "working_points"
        )
    result_dataset_real.to_netcdf(data_path / dataset_name)


def save_qoi(QOI_dict: dict[str, QOI], node_name: str, data_path: Path) -> None:
    """
    Save the node QOI for each element to a file.

    Args:
        QOI_dict (dict): The QOI dictionary to save.
        node_name (str): Name of the node being measured.
        data_path (Path): Path where the dataset will be saved.
    """
    measurement_id = data_path.stem[0:19]
    serialized_QOI_dict = {
        element: qoi.serialize() for element, qoi in QOI_dict.items()
    }
    file_path = data_path / f"{node_name}_qoi.json"
    with open(file_path, "w") as file:
        json.dump(serialized_QOI_dict, file, indent=2)


def save_figures(figures_list: list, node_name: str, data_path: Path):
    # TODO: as is, it doesn't support multiple couplers
    # TODO: pass the figures dict instead
    logger.info("Saving Plots")
    for fig_index, fig in enumerate(figures_list):
        node_name_stem = (
            f"{node_name}" if len(figures_list) == 1 else f"{node_name}_{fig_index}"
        )
        preview_path = data_path / f"{node_name_stem}_preview.png"
        full_path = data_path / f"{node_name_stem}.png"
        fig.savefig(preview_path, bbox_inches="tight", dpi=100)
        fig.savefig(full_path, bbox_inches="tight", dpi=400)
        logger.info(f"Plots saved to {preview_path} and {full_path}")
