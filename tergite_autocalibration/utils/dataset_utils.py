# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Tong Liu 2024
# (C) Copyright Michele Faucci Gianelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import pathlib
from collections.abc import Iterable
from datetime import datetime
from uuid import uuid4

import numpy as np
import xarray

from tergite_autocalibration.config.settings import DATA_DIR


def configure_dataset(
    raw_ds: xarray.Dataset,
    node,
) -> xarray.Dataset:
    """
    The dataset retrieved from the instrument coordinator is
    too bare-bones. Here the dims, coords and data_vars are configured
    """
    dataset = xarray.Dataset()

    keys = raw_ds.data_vars.keys()
    measurement_qubits = node.all_qubits
    schedule_samplespace = node.schedule_samplespace
    external_samplespace = node.reduced_external_samplespace

    samplespace = schedule_samplespace | external_samplespace

    # if hasattr(node, 'spi_samplespace'):
    #     spi_samplespace = node.spi_samplespace
    #     # merge the samplespaces: | is the dictionary merging operator
    #     samplespace = samplespace | spi_samplespace

    sweep_quantities = samplespace.keys()

    n_qubits = len(measurement_qubits)
    if node.name in [
        "ro_amplitude_three_state_optimization",
        "ro_frequency_three_state_optimization",
    ]:
        qubit_states = [0, 1, 2]
    elif node.name in [
        "ro_amplitude_two_state_optimization",
        "ro_frequency_two_state_optimization",
    ]:
        qubit_states = [0, 1]
    elif 'ssro' in node.name:
       qubit_states = ["c0", "c1", "c2"]  # for calibration points

    print(node.name)
    #if 'cz_param' in node.name:
    #    print("Here")
    #    return raw_ds

    for key in keys:
        key_indx = key % n_qubits  # this is to handle ro_opt_frequencies node where

        coords_dict = {}
        measured_qubit = measurement_qubits[key_indx]
        dimensions = node.dimensions
        print("node dimenstions are: ", dimensions)

        if 'ssro' in node.name:
            # TODO: We are not sure about this one
            # dimensions[0] += len(qubit_states)  # for calibration points
            shots = int(len(raw_ds[key].values[0]) / (np.product(dimensions)))
            coords_dict["shot"] = (
                "shot",
                range(shots),
                {"qubit": measured_qubit, "long_name": "shot", "units": "NA"},
            )
        # if node.name in [
        #     "cz_calibration_ssro",
        #     "cz_calibration_swap_ssro",
        #     "reset_calibration_ssro",
        #     "process_tomography_ssro",
        # ]:
        #     # TODO: We are not sure about this one
        #     dimensions[1] += len(qubit_states)  # for calibration points
        #     shots = int(len(raw_ds[key].values[0]) / (np.product(dimensions)))
        #     coords_dict["shot"] = (
        #         "shot",
        #         range(shots),
        #         {"qubit": measured_qubit, "long_name": "shot", "units": "NA"},
        #     )
        # elif node.name in [
        #     'tqg_randomized_benchmarking_ssro', 
        #     'tqg_randomized_benchmarking_interleaved_ssro', 
        #     'randomized_benchmarking_ssro' 
        #     ]:
        #     # TODO: We are not sure about this one
        #     dimensions[0] += len(qubit_states)  # for calibration points
        #     shots = int(len(raw_ds[key].values[0]) / (np.product(dimensions)))
        #     coords_dict['shot'] = ('shot', range(shots), {'qubit': measured_qubit, 'long_name': 'shot', 'units': 'NA'})
        
        for quantity in sweep_quantities:
            # eg ['q1','q2',...] or ['q1_q2','q3_q4',...] :
            settable_elements = samplespace[quantity].keys()
            #print('settable elements are: ', settable_elements)
            # distinguish if the settable is on a qubit or a coupler:
            if measured_qubit in settable_elements:
                element = measured_qubit
                element_type = "qubit"
            else:
                matching = [s for s in settable_elements if measured_qubit in s]
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
                "long_name": f"{coord_key}",
                "units": "NA",
            }
            #print('coord attributes is: ', coord_attrs)
            # if node.name in ['cz_calibration_ssro','cz_calibration_swap_ssro', 'reset_calibration_ssro'] and 'ramsey_phases' in quantity:
            #     settable_values = np.append(np.array([settable_values]), np.array([qubit_states]))
            # elif node.name in ['tqg_randomized_benchmarking_ssro', 'tqg_randomized_benchmarking_interleaved_ssro', 'randomized_benchmarking_ssro',]:
            #     settable_values = np.append(np.array([settable_values]), np.array([qubit_states]))


            # print(coord_attrs)

            if not isinstance(settable_values, Iterable):
                settable_values = np.array([settable_values])

            coords_dict[coord_key] = (coord_key, settable_values, coord_attrs)


        partial_ds = xarray.Dataset(coords=coords_dict)

        # print(partial_ds)

        data_values = raw_ds[key].values

        if (
            node.name == "ro_amplitude_two_state_optimization"
            or node.name == "ro_amplitude_three_state_optimization"
        ):
            loops = node.schedule_keywords["loop_repetitions"]
            for key in coords_dict.keys():
                if measured_qubit in key and "ro_amplitudes" in key:
                    ampls = coords_dict[key][1]
                elif measured_qubit in key and "qubit_states" in key:
                    states = coords_dict[key][1]
            data_values = reshufle_loop_dataset(data_values, ampls, states, loops)

        reshaping = reversed(node.dimensions)
        if node.name in ["ro_amplitude_optimization_gef"]:
            reshaping = [shots, dimensions[0], len(qubit_states)]
            data_values = data_values.reshape(*reshaping)
        elif 'ssro' in node.name:
            reshaping = np.array([shots])
            reshaping = np.append(reshaping, dimensions)
            data_values = data_values.reshape(*reshaping)
        else:
            data_values = data_values.reshape(*reshaping)
            data_values = np.transpose(data_values)
        attributes = {
            "qubit": measured_qubit,
            "long_name": f"y{measured_qubit}",
            "units": "NA",
        }
        partial_ds[f"y{measured_qubit}"] = (
            tuple(coords_dict.keys()),
            data_values,
            attributes,
        )

        # print(f'{partial_ds=}')
        dataset = xarray.merge([dataset, partial_ds])
        # print(f'{dataset=}')

    return dataset


def to_real_dataset(iq_dataset: xarray.Dataset) -> xarray.Dataset:
    ds = iq_dataset.expand_dims("ReIm", axis=-1)  # Add ReIm axis at the end
    ds = xarray.concat([ds.real, ds.imag], dim="ReIm")
    return ds


def reshufle_loop_dataset(initial_array: np.ndarray, ampls, states, loops: int):
    initial_shape = initial_array.shape
    initial_array = initial_array.flatten()
    states = np.unique(states)
    reshuffled_array = np.empty_like(initial_array)
    n_states = len(states)
    for i, el in enumerate(initial_array):
        measurements_per_loop = len(ampls) * n_states
        amplitude_group = (i % measurements_per_loop) // n_states
        new_index_group = amplitude_group * loops * n_states
        loop_number = i // measurements_per_loop
        new_index = new_index_group + loop_number * n_states + i % n_states
        reshuffled_array[new_index] = el
    reshuffled_array.reshape(*initial_shape)
    return reshuffled_array


def create_node_data_path(node) -> pathlib.Path:
    measurement_date = datetime.now()
    measurements_today = measurement_date.date().strftime("%Y%m%d")
    time_id = measurement_date.strftime("%Y%m%d-%H%M%S-%f")[:19]
    measurement_id = time_id + "-" + str(uuid4())[:6] + f"-{node.name}"
    data_path = pathlib.Path(DATA_DIR / measurements_today / measurement_id)
    return data_path


def retrieve_dummy_dataset(node) -> xarray.Dataset:
    if node.name == "resonator_spectroscopy":
        ds_path = "tergite_autocalibration/utils/dummy_datasets/20240510-131804-430-b5461c-resonator_spectroscopy/dataset.hdf5"
    elif node.name == "qubit_01_cw_spectroscopy":
        ds_path = "tergite_autocalibration/utils/dummy_datasets/20240510-131804-430-b5461c-resonator_spectroscopy/dataset.hdf5"
    elif node.name == "qubit_01_spectroscopy":
        ds_path = "tergite_autocalibration/utils/dummy_datasets/20240524-122934-019-3b1942-qubit_01_spectroscopy/dataset.hdf5"
    elif node.name == "rabi_oscillations":
        ds_path = "tergite_autocalibration/utils/dummy_datasets/20240524-123137-122-974556-rabi_oscillations/dataset.hdf5"
    elif node.name == "ramsey_correction":
        ds_path = "tergite_autocalibration/utils/dummy_datasets/20240312-092539-970-23d58e-ramsey_correction/dataset.hdf5"
    elif node.name == "adaptive_ramsey_correction":
        ds_path = "tergite_autocalibration/utils/dummy_datasets/20240312-092539-970-23d58e-ramsey_correction/dataset.hdf5"
    else:
        raise ValueError("Node does not have a stored dummy dataset")

    real_dataset = xarray.open_dataset(ds_path)
    dummy_ds = real_dataset.isel(ReIm=0) + 1j * real_dataset.isel(ReIm=1)

    # TODO probably this is not needed for newer datasets
    for data_var in dummy_ds.data_vars:
        dummy_ds[data_var].attrs.update({"qubit": data_var[1:]})
    for coord in dummy_ds.coords:
        dummy_ds[coord].attrs.update({"element_type": "qubit"})

    return dummy_ds


def save_dataset(
    result_dataset: xarray.Dataset, node_name: str, data_path: pathlib.Path
):
    data_path.mkdir(parents=True, exist_ok=True)
    measurement_id = data_path.stem[0:19]
    result_dataset = result_dataset.assign_attrs(
        {"name": node_name, "tuid": measurement_id}
    )
    result_dataset_real = to_real_dataset(result_dataset)
    # to_netcdf doesn't like complex numbers, convert to real/imag to save:
    count = 0
    dataset_name = "dataset_" + str(count) + ".hdf5"
    while (data_path / dataset_name).is_file():
        count += 1
        dataset_name = "dataset_" + str(count) + ".hdf5"
    result_dataset_real.to_netcdf(data_path / dataset_name)


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
