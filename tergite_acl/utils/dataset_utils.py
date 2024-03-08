import pathlib
from datetime import datetime
from uuid import uuid4

import numpy as np
import xarray

from tergite_acl.config.settings import DATA_DIR
from tergite_acl.lib.demod_channels import ParallelDemodChannels
from tergite_acl.lib.node_base import BaseNode


def configure_dataset(
        raw_ds: xarray.Dataset,
        node: 'BaseNode',
        ) -> xarray.Dataset:
    '''The dataset retrieved from the instrument coordinator  is
       too bare-bones. Here we configure the dims, coords and data_vars'''
    samplespace = node.samplespace
    parallel_demod_channels: ParallelDemodChannels = node.demod_channels

    dataset = xarray.Dataset()
    total_qubits = parallel_demod_channels.qubits_demod
    n_qubits = len(total_qubits)

    for i, demod_channel in enumerate(parallel_demod_channels.demod_channels):
        qubits = demod_channel.qubits
        channel_label = demod_channel.channel_label
        coords_dict = {}
        for quantity in samplespace:
            settable_elements = samplespace[quantity].keys()
            if not isinstance(samplespace[quantity], dict):
                settable_values = samplespace[quantity]
            elif channel_label in samplespace[quantity]:
                settable_values = samplespace[quantity][channel_label]
            else:
                settable_values = None
            if settable_values is not None:
                if channel_label in settable_elements:
                    element = channel_label
                    element_type = 'qubit'
                else:
                    matching = [s for s in settable_elements if channel_label in s]
                    if len(matching) == 1 and '_' in matching[0]:
                        element = matching[0]
                        element_type = 'coupler'
                    else:
                        raise (ValueError)
                coord_key = quantity + element
                settable_values = samplespace[quantity][element]
                coord_attrs = {element_type: element, 'long_name': f'{coord_key}', 'units': 'NA'}
                coords_dict[coord_key] = (coord_key, settable_values, coord_attrs)

                if hasattr(node, 'node_externals'):
                    coord_key = node.external_parameter_name + channel_label
                    coord_attrs = {'qubit': channel_label, 'long_name': f'{coord_key}', 'units': 'NA'}
                    coords_dict[coord_key] = (coord_key, np.array([node.external_parameter_value]), coord_attrs)

        dimensions = [len(samplespace[quantity][channel_label]) if isinstance(samplespace[quantity], dict) else len(samplespace[quantity]) for quantity in samplespace]
        reshaping = list(reversed(dimensions))
        data_values_multiqubit = []
        for qubit in qubits:
            idx = total_qubits.index(qubit)
            data_values = raw_ds[idx].values

            if node.name == 'ro_amplitude_two_state_optimization' or node.name == 'ro_amplitude_three_state_optimization':
                loops = node.node_dictionary['loop_repetitions']
                for key in coords_dict.keys():
                    if channel_label in key and 'ro_amplitudes' in key:
                        ampls = coords_dict[key][1]
                    elif channel_label in key and 'qubit_states' in key:
                        states = coords_dict[key][1]
                data_values = reshufle_loop_dataset(data_values, ampls, states, loops)


            data_values_reshape = data_values.reshape(*reshaping)
            data_values_multiqubit.append(data_values_reshape)
        data_values_multiqubit = np.array(data_values_multiqubit)
        data_values = tunneling_qubits(data_values_multiqubit)
        if len(qubits) == 1:
            attributes = {'qubit': qubits[0], 'long_name': f'y{qubit}', 'units': 'NA', 'channel_label': channel_label, 'repetitions':demod_channel.repetitions}
        else:
            attributes = {'qubits': qubits, 'long_name': '_'.join([f'y{qubit}' for qubit in qubits]), 'units': 'NA', 'channel_label': channel_label, 'repetitions':demod_channel.repetitions}

        # TODO ro_frequency_optimization requires multiple measurements per qubit
        is_frequency_opt = node.name == 'ro_frequency_two_state_optimization' or node.name == 'ro_frequency_three_state_optimization'
        if is_frequency_opt:
            qubit_states = [0,1,2]
            qubit_state = qubit_states[key // n_qubits]
            attributes['qubit_state'] = qubit_state

        partial_ds = xarray.Dataset(coords=coords_dict)
        partial_ds[f'y{channel_label}'] = (tuple(coords_dict.keys()), data_values, attributes)
        dataset = xarray.merge([dataset,partial_ds])
    return dataset

def to_real_dataset(iq_dataset: xarray.Dataset) -> xarray.Dataset:
    ds = iq_dataset.expand_dims('ReIm', axis=-1)  # Add ReIm axis at the end
    ds = xarray.concat([ds.real, ds.imag], dim='ReIm')
    return ds


def reshufle_loop_dataset(
    initial_array: np.ndarray, ampls, states, loops: int
    ):
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


def handle_ro_freq_optimization(complex_dataset: xarray.Dataset, states: list[int]) -> xarray.Dataset:
    new_ds = xarray.Dataset(coords=complex_dataset.coords, attrs=complex_dataset.attrs)
    new_ds = new_ds.expand_dims(dim={'qubit_state': states})
    # TODO this for every var and every coord. It might cause
    # performance issues for larger datasets
    for coord in complex_dataset.coords:
        this_qubit = complex_dataset[coord].attrs['qubit']
        attributes = {'qubit': this_qubit}
        values = []
        for var in complex_dataset.data_vars:
            if coord in complex_dataset[var].coords:
                values.append(complex_dataset[var].values)
        new_ds[f'y{this_qubit}'] = (('qubit_state', coord), np.vstack(values), attributes)
    return new_ds


def create_node_data_path(node):
    measurement_date = datetime.now()
    measurements_today = measurement_date.date().strftime('%Y%m%d')
    time_id = measurement_date.strftime('%Y%m%d-%H%M%S-%f')[:19]
    measurement_id = time_id + '-' + str(uuid4())[:6] + f'-{node.name}'
    data_path = pathlib.Path(DATA_DIR / measurements_today / measurement_id)
    return data_path


def save_dataset(result_dataset: xarray.Dataset, node, data_path: pathlib.Path):
    data_path.mkdir(parents=True, exist_ok=True)
    measurement_id = data_path.stem[0:19]
    result_dataset = result_dataset.assign_attrs({'name': node.name, 'tuid': measurement_id})
    result_dataset_real = to_real_dataset(result_dataset)
    # to_netcdf doesn't like complex numbers, convert to real/imag to save:
    result_dataset_real.to_netcdf(data_path / 'dataset.hdf5')

def tunneling_qubits(data_values:np.ndarray) -> np.ndarray:
    """
    Add a new data_var prob.
    Convert S21 into probs of states.
    """
    if data_values.shape[0] == 1:
        data_values = data_values[0]
        dims = len(data_values.shape)
        return np.moveaxis(data_values, range(dims), range(dims-1, -1, -1))
    else:
        dims = len(data_values.shape)
        return np.moveaxis(data_values, range(1, dims), range(dims-1, 0, -1))