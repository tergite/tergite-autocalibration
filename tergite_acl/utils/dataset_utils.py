import xarray
import numpy as np
from datetime import datetime
from uuid import uuid4
import pathlib
from tergite_acl.config.settings import DATA_DIR
from tergite_acl.lib.demod_channels import ParallelDemodChannels


def configure_dataset(
        raw_ds: xarray.Dataset,
        node,
    ) -> xarray.Dataset:
    '''
    The dataset retrieved from the instrument coordinator is
    too bare-bones. Here the dims, coords and data_vars are configured
    '''
    dataset = xarray.Dataset()

    keys = raw_ds.data_vars.keys()
    measurement_qubits = node.all_qubits
    samplespace = node.samplespace

    # if hasattr(node, 'spi_samplespace'):
    #     spi_samplespace = node.spi_samplespace
    #     # merge the samplespaces: | is the dictionary merging operator
    #     samplespace = samplespace | spi_samplespace

    sweep_quantities = samplespace.keys()

    n_qubits = len(measurement_qubits)

    for key in keys:
        key_indx = key%n_qubits # this is to handle ro_opt_frequencies node where
        # there are 2 or 3 measurements (i.e 2 or 3 Datarrays) for each qubit
        coords_dict = {}
        measured_qubit = measurement_qubits[key_indx]

        for quantity in sweep_quantities :

            # eg ['q1','q2',...] or ['q1_q2','q3_q4',...] :
            settable_elements = samplespace[quantity].keys()

            # distinguish if the settable is on a quabit or a coupler:
            if measured_qubit in settable_elements:
                element = measured_qubit
                element_type = 'qubit'
            else:
                matching = [s for s in settable_elements if measured_qubit in s]
                if len(matching) == 1 and '_' in matching[0]:
                    element = matching[0]
                    element_type = 'coupler'
                else:
                    raise(ValueError)

            coord_key = quantity + element
            settable_values = samplespace[quantity][element]
            coord_attrs = {element_type: element, 'long_name': f'{coord_key}', 'units': 'NA'}

            coords_dict[coord_key] = (coord_key, settable_values, coord_attrs)

        if hasattr(node, 'node_externals'):
            coord_key = node.external_parameter_name + measured_qubit
            coord_attrs = {'qubit':measured_qubit, 'long_name': f'{coord_key}', 'units': 'NA'}
            coords_dict[coord_key] = (coord_key, np.array([node.external_parameter_value]), coord_attrs)

        partial_ds = xarray.Dataset(coords=coords_dict)

        data_values = raw_ds[key].values


        if node.name == 'ro_amplitude_two_state_optimization' or node.name == 'ro_amplitude_three_state_optimization':
            loops = node.node_dictionary['loop_repetitions']
            for key in coords_dict.keys():
                if measured_qubit in key and 'ro_amplitudes' in key:
                    ampls = coords_dict[key][1]
                elif measured_qubit in key and 'qubit_states' in key:
                    states = coords_dict[key][1]
            data_values = reshufle_loop_dataset(data_values, ampls, states, loops)


        # TODO this is not safe:
        # This assumes that the inner settable variable is placed
        # at the first position in the samplespace
        reshaping = reversed(node.dimensions)
        data_values = data_values.reshape(*reshaping)
        data_values = np.transpose(data_values)
        attributes = {'qubit': measured_qubit, 'long_name': f'y{measured_qubit}', 'units': 'NA'}
        qubit_state = ''
        # if 'ro_opt_frequencies' in list(sweep_quantities):
        # if 'ro_opt_frequencies' in list(sweep_quantities):
        #     qubit_states = [0,1,2]

        # TODO ro_frequency_optimization requires multiple measurements per qubit
        is_frequency_opt = node.name == 'ro_frequency_two_state_optimization' or node.name == 'ro_frequency_three_state_optimization'
        if is_frequency_opt:
            qubit_states = [0,1,2]
            qubit_state = qubit_states[key // n_qubits]
            attributes['qubit_state'] = qubit_state

        partial_ds[f'y{measured_qubit}{qubit_state}'] = (tuple(coords_dict.keys()), data_values, attributes)
        dataset = xarray.merge([dataset,partial_ds])
    return dataset

def configure_dataset_via_meas_ctrl(
        raw_ds: xarray.Dataset,
        samplespace: dict[str, dict[str,np.ndarray]],
        parallel_demod_channels: ParallelDemodChannels
        ) -> xarray.Dataset:
    '''The dataset retrieved from the instrument coordinator  is
       too bare-bones. Here we configure the dims, coords and data_vars'''

    dataset = xarray.Dataset()
    total_qubits = parallel_demod_channels.qubits_demod
    assert len(raw_ds.data_vars) == 2 * len(total_qubits), f"Please check the measure in the schedule function. The qubits to be demodulated are {total_qubits}."
    for i, demod_channel in enumerate(parallel_demod_channels.demod_channels):
        qubits = demod_channel.qubits
        channel_label = demod_channel.channel_label
        coords_dict = {}
        for quantity in samplespace:
            if not isinstance(samplespace[quantity], dict):
                settable_values = samplespace[quantity]
            elif channel_label in samplespace[quantity]:
                settable_values = samplespace[quantity][channel_label]
            else:
                settable_values = None
            if settable_values is not None:
                coord_key = quantity + channel_label
                coord_attrs = {'qubit':demod_channel.qubits, 'long_name': f'{coord_key}', 'units': 'NA', 'channel_label': channel_label}
                coords_dict[coord_key] = (coord_key, settable_values, coord_attrs)

        dimensions = [len(samplespace[quantity][channel_label]) if isinstance(samplespace[quantity], dict) else len(samplespace[quantity]) for quantity in samplespace]
        reshaping = list(reversed(dimensions))
        data_values_multiqubit = []
        for qubit in qubits:
            idx = total_qubits.index(qubit)
            # TODO: Figure out the name of the data_var stored in the dataset
            # key0, key1 = f'y{2*idx}', f'y{2*idx+1}'
            # if raw_ds[key0].attrs['name'] == 'magn':
            #     data_values = raw_ds[key0].values * np.exp(1j * raw_ds[key1].values / 180 * np.pi)
            # else:
            #     data_values = raw_ds[key0].values + 1j * raw_ds[key1].values
            data_values_reshape = data_values.reshape(*reshaping)
            data_values_multiqubit.append(data_values_reshape)
        data_values_multiqubit = np.array(data_values_multiqubit)
        data_values = np.transpose(data_values_reshape)
        if len(qubits) == 1:
            attributes = {'qubit': qubits[0], 'long_name': f'y{qubit}', 'units': 'NA', 'channel_label': channel_label, 'repetitions':demod_channel.repetitions}
        else:
            attributes = {'qubits': qubits, 'long_name': '_'.join([f'y{qubit}' for qubit in qubits]), 'units': 'NA', 'channel_label': channel_label, 'repetitions':demod_channel.repetitions}
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
