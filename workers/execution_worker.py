'''Retrieve the compiled schedule and run it'''
from datetime import datetime
import pathlib
from time import sleep
from uuid import uuid4
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
from qblox_instruments.ieee488_2 import DummyBinnedAcquisitionData
colorama_init()

from quantify_scheduler.instrument_coordinator.instrument_coordinator import CompiledSchedule
from logger.tac_logger import logger

from qblox_instruments import Cluster, ClusterType
from quantify_scheduler.instrument_coordinator import InstrumentCoordinator
from quantify_scheduler.instrument_coordinator.components.qblox import ClusterComponent
import xarray
from utilities.status import ClusterStatus
import numpy as np
import threading
import tqdm
from utilities.root_path import data_directory
from calibration_schedules.time_of_flight import measure_time_of_flight
from config_files.settings import lokiA_IP

import redis

redis_connection = redis.Redis(decode_responses=True)

def configure_dataset(
        raw_ds: xarray.Dataset,
        samplespace: dict[str, dict[str,np.ndarray]],
        ) -> xarray.Dataset:
    '''The dataset retrieved from the instrument coordinator  is
       too bare-bones. Here we configure the dims, coords and data_vars'''
    logger.info('Configuring Dataset')
    dataset = xarray.Dataset()
    # keys = sorted(list(raw_ds.data_vars.keys()))
    #TODO instead of doing all these gymnastics just set attributes to the samplespace
    keys = raw_ds.data_vars.keys()
    sweep_quantities = samplespace.keys() # for example 'ro_frequencies', 'ro_amplitudes' ,...
    sweep_parameters = list(samplespace.values())[0]
    qubits = list(sweep_parameters.keys())
    n_qubits = len(qubits)
    if 'ro_opt_frequencies' in list(sweep_quantities):
        qubit_states = [0,1,2]

    for key in keys:
        key_indx = key%n_qubits
        coords_dict = {}
        this_qubit = qubits[key_indx]
        for quantity in sweep_quantities :
            coord_key = quantity+this_qubit
            settable_values = samplespace[quantity][this_qubit]
            coord_attrs = {'qubit':this_qubit, 'long_name': f'{coord_key}', 'units': 'NA'}
            coords_dict[coord_key] = (coord_key, settable_values, coord_attrs)
        partial_ds = xarray.Dataset(coords=coords_dict)
        #breakpoint()
        dimensions = [len(samplespace[quantity][this_qubit]) for quantity in sweep_quantities]
        # TODO this is not safe:
        # This assumes that the inner settable variable is placed
        # at the first position in the samplespace

        reshaping = reversed(dimensions)
        data_values = raw_ds[key].values.reshape(*reshaping)
        data_values = np.transpose(data_values)
        attributes = {'qubit': this_qubit, 'long_name': f'y{this_qubit}', 'units': 'NA'}
        qubit_state = ''
        if 'ro_opt_frequencies' in list(sweep_quantities):
            qubit_state = qubit_states[key // n_qubits]
            attributes['qubit_state'] = qubit_state
        partial_ds[f'y{this_qubit}_real{qubit_state}'] = (tuple(coords_dict.keys()), data_values.real, attributes)
        partial_ds[f'y{this_qubit}_imag{qubit_state}'] = (tuple(coords_dict.keys()), data_values.imag, attributes)
        dataset = xarray.merge([dataset,partial_ds])
    return dataset

def to_complex_dataset(iq_dataset: xarray.Dataset) -> xarray.Dataset:
    dataset_dict = {}
    complex_ds = xarray.Dataset(coords=iq_dataset.coords)
    for var in iq_dataset.data_vars.keys():
        this_qubit = iq_dataset[var].attrs['qubit']
        attributes = {'qubit': this_qubit}
        this_state = ''
        if 'qubit_state' in iq_dataset[var].attrs:
            qubit_state = iq_dataset[var].attrs["qubit_state"]
            this_state = qubit_state
            attributes['qubit_state'] = qubit_state

        #TODO this could be better:
        #TODO since the retrieved dataset is already complex
        # there is no point in converting to (real, imag) and then back to complex
        if not this_qubit in dataset_dict:
            dataset_dict[this_qubit] = {}
        current_values = iq_dataset[var].values
        if 'real' in var:
            dataset_dict[this_qubit]['real'] = current_values
        elif 'imag' in var:
            dataset_dict[this_qubit]['imag'] = current_values

        if 'real' in dataset_dict[this_qubit] and 'imag' in dataset_dict[this_qubit]:
            qubit_coords = iq_dataset[f'y{this_qubit}_real{this_state}'].coords
            complex_values = dataset_dict[this_qubit]['real'] + 1j*dataset_dict[this_qubit]['imag']
            complex_ds[f'y{this_qubit}{this_state}'] = (qubit_coords, complex_values, attributes)

    return complex_ds

def handle_ro_freq_optimization(complex_dataset: xarray.Dataset) -> xarray.Dataset:
    new_ds = xarray.Dataset(coords=complex_dataset.coords, attrs=complex_dataset.attrs)
    new_ds = new_ds.expand_dims(dim={'qubit_state': [0,1]})
    #TODO this for every var and every coord. It might cause
    # performance issues for larger datasets
    for coord in complex_dataset.coords:
        this_qubit = complex_dataset[coord].attrs['qubit']
        attributes = {'qubit': this_qubit}
        values = []
        for var in complex_dataset.data_vars:
            if coord in complex_dataset[var].coords:
                values.append(complex_dataset[var].values)
        new_ds[f'y{this_qubit}'] = (('qubit_state',coord), np.vstack(values), attributes)

    return new_ds
    # xarray.concat([result_dataset_complex.yq160, result_dataset_complex.yq161],'ro_opt_frequenciesq16', combine_attrs='drop_conflicts')

def measure(
        compiled_schedule: CompiledSchedule,
        schedule_duration: float,
        samplespace: dict,
        node: str,
        cluster_status: ClusterStatus = ClusterStatus.real
    ) -> xarray.Dataset:

    logger.info('Starting measurement')

    print(f'{Fore.BLUE}{Style.BRIGHT}Measuring node: {node} , duration: {schedule_duration:.2f}s{Style.RESET_ALL}')

    Cluster.close_all()
    if cluster_status == ClusterStatus.dummy:
        dummy = {str(mod): ClusterType.CLUSTER_QCM_RF for mod in range(1,16)}
        dummy["16"] = ClusterType.CLUSTER_QRM_RF
        dummy["17"] = ClusterType.CLUSTER_QRM_RF
        dimension = 1
        for subspace in samplespace.values():
            dimension *= len( list(subspace.values())[0] )

        dummy_data = [ DummyBinnedAcquisitionData(data=(1,6),thres=1,avg_cnt=1) for _ in range(dimension) ]
        dummy_data_1 = [ DummyBinnedAcquisitionData(data=(1,3),thres=1,avg_cnt=1) for _ in range(dimension) ]
        clusterA = Cluster("clusterA", dummy_cfg=dummy)
        clusterA.set_dummy_binned_acquisition_data(16,sequencer=0,acq_index_name="0",data=dummy_data)
        clusterA.set_dummy_binned_acquisition_data(16,sequencer=1,acq_index_name="1",data=dummy_data)
        clusterA.set_dummy_binned_acquisition_data(16,sequencer=2,acq_index_name="2",data=dummy_data)

        if node=='ro_frequency_optimization':
            clusterA.set_dummy_binned_acquisition_data(16,sequencer=0,acq_index_name="3",data=dummy_data_1)
            clusterA.set_dummy_binned_acquisition_data(16,sequencer=1,acq_index_name="4",data=dummy_data_1)
            clusterA.set_dummy_binned_acquisition_data(16,sequencer=2,acq_index_name="5",data=dummy_data_1)

    elif cluster_status == ClusterStatus.real:
        clusterA = Cluster("clusterA", lokiA_IP)

    if node == 'tof':
        result_dataset = measure_time_of_flight(clusterA)
        return result_dataset
    lab_ic = InstrumentCoordinator('lab_ic')
    lab_ic.add_component(ClusterComponent(clusterA))
    lab_ic.timeout(222)

    def run_measurement() -> None:
        lab_ic.prepare(compiled_schedule)
        lab_ic.start()
        lab_ic.wait_done(timeout_sec=600)

    def display_progress():
        steps = int(schedule_duration * 5)
        if cluster_status == ClusterStatus.dummy:
            progress_sleep = 0.004
        elif cluster_status == ClusterStatus.real :
            progress_sleep = 0.2
        for _ in tqdm.tqdm(range(steps), desc=node, colour='blue'):
            sleep(progress_sleep)


    thread_tqdm = threading.Thread(target=display_progress)
    thread_tqdm.start()
    thread_lab = threading.Thread(target=run_measurement)
    thread_lab.start()
    thread_lab.join()
    thread_tqdm.join()

    raw_dataset: xarray.Dataset = lab_ic.retrieve_acquisition()
    logger.info('Raw dataset acquired')

    result_dataset = configure_dataset(raw_dataset, samplespace)

    measurement_date = datetime.now()
    measurements_today = measurement_date.date().strftime('%Y%m%d')
    measurement_id = measurement_date.strftime('%Y%m%d-%H%M%S-%f')[:19] + '-' + str(uuid4())[:6] + f'-{node}'
    data_path = pathlib.Path(data_directory / measurements_today / measurement_id)
    data_path.mkdir(parents=True, exist_ok=True)

    result_dataset = result_dataset.assign_attrs({'name': node, 'tuid': measurement_id})

    result_dataset.to_netcdf(data_path / 'dataset.hdf5')

    result_dataset_complex = to_complex_dataset(result_dataset)
    if node=='ro_frequency_optimization':
        result_dataset_complex = handle_ro_freq_optimization(result_dataset_complex)

    lab_ic.stop()
    logger.info('Finished measurement')

    return result_dataset_complex
