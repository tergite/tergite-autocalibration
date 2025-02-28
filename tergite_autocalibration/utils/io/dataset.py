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
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Union
from uuid import uuid4

import numpy as np
import xarray

from tergite_autocalibration.config.globals import CONFIG
from tergite_autocalibration.utils.logging import logger


def configure_dataset(
    raw_ds: xarray.Dataset,
    node,
) -> xarray.Dataset:
    """
    The dataset retrieved from the instrument coordinator is
    too bare-bones. Here the dims, coords and data_vars are configured
    """
    dataset = xarray.Dataset(attrs={"elements": []})

    raw_ds_keys = raw_ds.data_vars.keys()
    measurement_qubits = node.all_qubits
    samplespace = node.schedule_samplespace

    sweep_quantities = samplespace.keys()

    n_qubits = len(measurement_qubits)

    for key in raw_ds_keys:
        key_indx = key % n_qubits  # this is to handle ro_opt_frequencies node where

        coords_dict = {}
        measured_qubit = measurement_qubits[key_indx]
        dimensions = node.dimensions

        # TODO: this is flagged for removal.
        if "ssro" in node.name and node.name != "randomized_benchmarking_ssro":
            shots = int(len(raw_ds[key].values[0]) / (np.product(dimensions)))
            coords_dict["shot"] = (
                "shot",
                range(shots),
                {"qubit": measured_qubit, "long_name": "shot", "units": "NA"},
            )

        for quantity in sweep_quantities:
            # eg settable_elements -> ['q1','q2',...] or ['q1_q2','q3_q4',...] :
            settable_elements = samplespace[quantity].keys()

            # distinguish if the settable is on a qubit or a coupler:
            if measured_qubit in settable_elements:
                element = measured_qubit
                element_type = "qubit"
            else:
                matching = [s for s in settable_elements if measured_qubit in s]
                # TODO: len(matching) == 1 implies that we operate on only 1 coupler.
                # To be changed in future
                if len(matching) == 1 and "_" in matching[0]:
                    element = matching[0]
                    element_type = "coupler"
                else:
                    raise (ValueError)

            coord_key = quantity + element

            settable_values = samplespace[quantity][element]
            coord_attrs = {
                "element_type": element_type,  # 'element_type' is ether 'qubit' or 'coupler'
                element_type: element,
                "measured_qubit": measured_qubit,
                "long_name": f"{coord_key}",
                "units": "NA",
            }

            if not isinstance(settable_values, Iterable):
                settable_values = np.array([settable_values])

            coords_dict[coord_key] = (coord_key, settable_values, coord_attrs)

        if node.loops is not None:
            coords_dict["loops"] = (
                "loops",
                np.arange(node.loops),
                {"element_type": "NA"},
            )

        partial_ds = xarray.Dataset(coords=coords_dict)

        data_values = raw_ds[key].values

        reshaping = reversed(node.dimensions)

        # TODO: flagged for removal
        if "ssro" in node.name and node.name != "randomized_benchmarking_ssro":
            reshaping = np.array([shots])
            reshaping = np.append(reshaping, dimensions)
            data_values = data_values.reshape(*reshaping)
        else:
            data_values = data_values.reshape(*node.dimensions, order="F")

        # determine if this dataarray examines a qubit or a coupler:
        # TODO: this needs improvement
        element = measured_qubit
        if node.couplers is not None:
            element = node.couplers[0]

        attributes = {
            "qubit": measured_qubit,
            "element": element,
            "long_name": f"y{measured_qubit}",
            "units": "NA",
        }
        partial_ds[f"y{measured_qubit}"] = (
            tuple(coords_dict.keys()),
            data_values,
            attributes,
        )

        dataset = xarray.merge([dataset, partial_ds])
        dataset.attrs["elements"].append(element)

    return dataset


def to_real_dataset(iq_dataset: xarray.Dataset) -> xarray.Dataset:
    ds = iq_dataset.expand_dims("ReIm", axis=-1)  # Add ReIm axis at the end
    ds = xarray.concat([ds.real, ds.imag], dim="ReIm")
    return ds


def create_node_data_path(node) -> Path:
    """
    Create the folder where measurement results, plots and logs specific to the node are stored.

    Args:
        node (BaseNode): to create a data path for.

    Returns:
        Path to the measurement log folder as Path.

    """
    now_ = datetime.now()
    measurement_id = (
        f"{now_.strftime('%Y%m%d-%H%M%S-%f')[:19]}-{str(uuid4())[:6]}-{node.name}"
    )
    data_path = Path(os.path.join(CONFIG.run.log_dir, measurement_id))
    return data_path

def scrape_and_copy_hdf5_files(scrape_directory: Union[Path, str], target_directory: Union[Path, str]):
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
