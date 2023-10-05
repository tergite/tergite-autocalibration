'''Retrieve the compiled schedule and run it'''
from quantify_scheduler.instrument_coordinator.instrument_coordinator import CompiledSchedule
from logger.tac_logger import logger
from qblox_instruments import Cluster, ClusterType
from quantify_scheduler.instrument_coordinator import InstrumentCoordinator
from quantify_scheduler.instrument_coordinator.components.qblox import ClusterComponent
import xarray
from utilities.status import ClusterStatus
from workers.worker_utils import configure_dataset, handle_ro_freq_optimization, to_real_dataset
import numpy as np
import threading
import tqdm
from utilities.root_path import data_directory
from workers.dummy_setup import dummy_cluster
from calibration_schedules.time_of_flight import measure_time_of_flight
from config_files.settings import lokiA_IP
import redis
from datetime import datetime
import pathlib
from time import sleep
from uuid import uuid4
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
colorama_init()

redis_connection = redis.Redis(decode_responses=True)

def measure(
        compiled_schedule: CompiledSchedule,
        schedule_duration: float,
        samplespace: dict,
        node: str,
        measurement_index: [int, int] = [0,0],
        cluster_status: ClusterStatus = ClusterStatus.real
    ) -> xarray.Dataset:

    logger.info('Starting measurement')

    current_measurement = ''
    if measurement_index[1] > 1:
        current_measurement = f'{measurement_index[0]} / {measurement_index[1]}'

    print_message = f'{Fore.BLUE}{Style.BRIGHT}Measuring node: {node} {current_measurement}'
    print_message += f'duration: {schedule_duration:.2f}s{Style.RESET_ALL}'
    print(print_message)

    Cluster.close_all()

    if cluster_status == ClusterStatus.dummy:
        clusterA = dummy_cluster(samplespace)

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
    time_id = measurement_date.strftime('%Y%m%d-%H%M%S-%f')[:19]
    measurement_id = time_id + '-' + str(uuid4())[:6] + f'-{node}'
    data_path = pathlib.Path(data_directory / measurements_today / measurement_id)
    data_path.mkdir(parents=True, exist_ok=True)

    result_dataset = result_dataset.assign_attrs({'name': node, 'tuid': measurement_id})

    result_dataset_real = to_real_dataset(result_dataset)
    #to_netcdf doesn't like complex numbers, convert to real/imag to save:
    result_dataset_real.to_netcdf(data_path / 'dataset.hdf5')

    if node=='ro_frequency_optimization':
        result_dataset= handle_ro_freq_optimization(result_dataset,states=[0,1])
    elif node=='ro_frequency_optimization_gef':
        result_dataset= handle_ro_freq_optimization(result_dataset,states=[0,1,2])

    lab_ic.stop()
    logger.info('Finished measurement')

    return result_dataset
