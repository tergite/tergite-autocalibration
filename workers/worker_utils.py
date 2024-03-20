import xarray
import numpy as np
from datetime import datetime
from uuid import uuid4
import pathlib
from utilities.root_path import data_directory


def configure_dataset(
        name: str,
        raw_ds: xarray.Dataset,
        samplespace: dict[str, dict[str,np.ndarray]],
        ) -> xarray.Dataset:
    '''The dataset retrieved from the instrument coordinator  is
       too bare-bones. Here we configure the dims, coords and data_vars'''

    dataset = xarray.Dataset()

    keys = raw_ds.data_vars.keys()
    sweep_quantities = samplespace.keys() # for example 'ro_frequencies', 'ro_amplitudes' ,...
    sweep_parameters = list(samplespace.values())
    qubits = []
    for sweep in sweep_parameters:
        qubits += list(sweep.keys())
    dublicates = set()
    # for soem measurements a qubit can appear in multiple keys. Here we filter the dublicates
    # TODO better explanation
    qubits = [q for q in qubits if not (q in dublicates or dublicates.add(q))]
    n_qubits = len(qubits)
    # if 'ro_opt_frequencies' in list(sweep_quantities):
    if name in ['ro_amplitude_optimization_gef', 'ro_frequency_optimization_gef']:
        qubit_states = [0,1,2]
    elif name in ['ro_amplitude_optimization', 'ro_frequency_optimization']:
        qubit_states = [0,1]
    elif name in ['cz_calibration_ssro','reset_calibration_ssro']:
        qubit_states = ['c0','c1','c2'] # for calibration points
    key_list = [key for key in raw_ds.data_vars.keys()]
    for idx,key in enumerate(keys):
        if name in ['ro_frequency_optimization_gef',]:
            key_indx = key%n_qubits # this is to handle ro_opt_frequencies node where
            # there are 2 or 3 measurements (i.e 2 or 3 Datarrays) for each qubit
        else:
            key_indx = idx%n_qubits # and also start from 0
        coords_dict = {}
        qubit = qubits[key_indx]
        dimensions = [len(samplespace[quantity][qubit]) for quantity in sweep_quantities]
        if name in ['ro_amplitude_optimization_gef']:
            # shots = 1
            # shots = int(len(raw_ds[key].values))
            shots = int(len(raw_ds[key].values[0])/(dimensions[0]*len(qubit_states)))
            coords_dict['shot'] = ('shot',range(shots),{'qubit':qubit, 'long_name': 'shot', 'units': 'NA'})
        elif name in ['cz_calibration_ssro','reset_calibration_ssro']:
            dimensions[1] += len(qubit_states) # for calibration points
            shots = int(len(raw_ds[key].values[0])/(np.product(dimensions)))
            coords_dict['shot'] = ('shot',range(shots),{'qubit':qubit, 'long_name': 'shot', 'units': 'NA'})
 
        for quantity in sweep_quantities :
            coord_key = quantity+qubit
            if qubit in samplespace[quantity]:
                settable_values = samplespace[quantity][qubit]
                # for node with calibration points [g,e,f], only change the ramey_phase samplespace
                if name in ['cz_calibration_ssro','reset_calibration_ssro'] and 'ramsey_phases' in quantity:
                    settable_values = np.append(np.array([settable_values]),np.array([qubit_states]))
            else:
                continue
            coord_attrs = {'qubit':qubit, 'long_name': f'{coord_key}', 'units': 'NA'}
            coords_dict[coord_key] = (coord_key, settable_values, coord_attrs)
        
        if name in ['ro_amplitude_optimization_gef']:
            coords_dict['state'] = ('state',qubit_states,{'qubit':qubit, 'long_name': 'state', 'units': 'NA'})
            
        partial_ds = xarray.Dataset(coords=coords_dict)
        # TODO this is not safe:
        # This assumes that the inner settable variable is placed
        # at the first position in the samplespace

        reshaping = reversed(dimensions)
        if name in ['ro_amplitude_optimization_gef']:
            reshaping = [shots,dimensions[0],len(qubit_states)]
            data_values = raw_ds[key].values.reshape(*reshaping)
        elif name in ['cz_calibration_ssro','reset_calibration_ssro']:
            reshaping = np.array([shots])
            reshaping = np.append(reshaping,dimensions)
            data_values = raw_ds[key].values.reshape(*reshaping)
        else:
            data_values = raw_ds[key].values.reshape(*reshaping)
            data_values = np.transpose(data_values)
        attributes = {'qubit': qubit, 'long_name': f'y{qubit}', 'units': 'NA'}
        qubit_state = ''
        if name in ['ro_amplitude_optimization_gef', 'ro_frequency_optimization_gef']:
            qubit_state = qubit_states[key // n_qubits]
            attributes['qubit_state'] = qubit_state
        #real_data_array = xarray.DataArray(
        #                     data=data_values.real,
        #                     coords=coords_dict,
        #                     dims='ro_frequencies',
        #                     attrs=attributes
        #                )
        #partial_ds[f'y{qubit}_real{qubit_state}'] = real_data_array
        # breakpoint()
        partial_ds[f'y{qubit}{qubit_state}'] = (tuple(coords_dict.keys()), data_values, attributes)
        dataset = xarray.merge([dataset,partial_ds])
        # breakpoint()

    return dataset


def to_real_dataset(iq_dataset: xarray.Dataset) -> xarray.Dataset:
    ds = iq_dataset.expand_dims('ReIm', axis=-1)  # Add ReIm axis at the end
    ds = xarray.concat([ds.real, ds.imag], dim='ReIm')
    return ds


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
        # print(new_ds)
        # print(coord,np.vstack(values),attributes)
        new_ds[f'y{this_qubit}'] = (('qubit_state', coord), np.vstack(values), attributes)
    return new_ds

def create_node_data_path(node):
    measurement_date = datetime.now()
    measurements_today = measurement_date.date().strftime('%Y%m%d')
    time_id = measurement_date.strftime('%Y%m%d-%H%M%S-%f')[:19]
    measurement_id = time_id + '-' + str(uuid4())[:6] + f'-{node.name}'
    data_path = pathlib.Path(data_directory / measurements_today / measurement_id)
    return data_path


def save_dataset(result_dataset: xarray.Dataset, node, data_path: pathlib.Path):
    data_path.mkdir(parents=True, exist_ok=True)
    measurement_id = data_path.stem[0:19]
    result_dataset = result_dataset.assign_attrs({'name': node.name, 'tuid': measurement_id})
    result_dataset_real = to_real_dataset(result_dataset)
    # to_netcdf doesn't like complex numbers, convert to real/imag to save:
    #if 'multi' in node.name: breakpoint()
    result_dataset_real.to_netcdf(data_path / 'dataset.hdf5')
