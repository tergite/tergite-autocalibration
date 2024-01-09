import xarray
import numpy as np
from datetime import datetime
from uuid import uuid4
from enum import Enum
import pathlib
from utilities.root_path import data_directory


class SweepType(Enum):
    ClusterSweepOnQubits = 1 # Sweeps with the cluster.  All the single qubit operations are of these type.
    ClusterSweepOnCouplers = 2 # Sweeps with the cluster but applied on a coupler. E.g. CZ Chevron measurements.
    SPI_and_Cluster_Sweep = 3 # Sweeps using the SPI and the cluster. Used on Coupler spectroscopy.



def configure_dataset(
        raw_ds: xarray.Dataset,
        node,
    ) -> xarray.Dataset:
    '''
    The dataset retrieved from the instrument coordinator  is
    too bare-bones. Here we configure the dims, coords and data_vars
    '''

    if hasattr(node, 'coupler_samplespace'):
        sweep_type = SweepType.ClusterSweepOnCouplers
    elif hasattr(node, 'spi_samplespace'):
        sweep_type = SweepType.SPI_and_Cluster_Sweep
        spi_samplespace = node.spi_samplespace
        spi_sweep_quantities = spi_samplespace.keys() # for example 'dc_currents'
    elif hasattr(node, 'samplespace') and not hasattr(node, 'spi_samplespace'):
        sweep_type = SweepType.ClusterSweepOnQubits

    dataset = xarray.Dataset()

    def get_coupler_from_qubit(qubit: str):
        for bus in node.couplers:
            if qubit in bus:
                coupler = bus
        return coupler


    keys = raw_ds.data_vars.keys()
    measurement_qubits = node.all_qubits
    samplespace = node.samplespace
    sweep_quantities = samplespace.keys() # for example 'ro_frequencies', 'ro_amplitudes' ,...

    n_qubits = len(measurement_qubits)
    if 'ro_opt_frequencies' in list(sweep_quantities):
        qubit_states = [0,1,2]

    for key in keys:
        key_indx = key%n_qubits # this is to handle ro_opt_frequencies node where
        # there are 2 or 3 measurements (i.e 2 or 3 Datarrays) for each qubit
        coords_dict = {}
        qubit = measurement_qubits[key_indx]

        for quantity in sweep_quantities :
            if sweep_type == SweepType.ClusterSweepOnCouplers:
                coupler = get_coupler_from_qubit(qubit)
                coord_key = quantity + coupler
                settable_values = samplespace[quantity][coupler]
            elif sweep_type == SweepType.ClusterSweepOnQubits:
                coord_key = quantity + qubit
                settable_values = samplespace[quantity][qubit]
            else:
                raise(ValueError)

            coord_attrs = {'qubit':qubit, 'long_name': f'{coord_key}', 'units': 'NA'}
            coords_dict[coord_key] = (coord_key, settable_values, coord_attrs)

        if sweep_type == SweepType.SPI_and_Cluster_Sweep:
            for quantity in spi_sweep_quantities:
                coupler = get_coupler_from_qubit(qubit)
                coord_key = quantity + coupler
                settable_values = spi_samplespace[quantity][coupler]


        partial_ds = xarray.Dataset(coords=coords_dict)
        dimensions = [len(samplespace[quantity][qubit]) for quantity in sweep_quantities]

        # TODO this is not safe:
        # This assumes that the inner settable variable is placed
        # at the first position in the samplespace

        reshaping = reversed(dimensions)
        data_values = raw_ds[key].values.reshape(*reshaping)
        data_values = np.transpose(data_values)
        attributes = {'qubit': qubit, 'long_name': f'y{qubit}', 'units': 'NA'}
        qubit_state = ''
        if 'ro_opt_frequencies' in list(sweep_quantities):
            qubit_state = qubit_states[key // n_qubits]
            attributes['qubit_state'] = qubit_state
        #breakpoint()
        #real_data_array = xarray.DataArray(
        #                     data=data_values.real,
        #                     coords=coords_dict,
        #                     dims='ro_frequencies',
        #                     attrs=attributes
        #                )
        #partial_ds[f'y{qubit}_real{qubit_state}'] = real_data_array

        partial_ds[f'y{qubit}{qubit_state}'] = (tuple(coords_dict.keys()), data_values, attributes)
        dataset = xarray.merge([dataset,partial_ds])
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
    result_dataset_real.to_netcdf(data_path / 'dataset.hdf5')
