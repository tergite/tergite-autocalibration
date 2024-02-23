'''Retrieve the compiled schedule and run it'''
import threading
from quantify_scheduler.instrument_coordinator.instrument_coordinator import CompiledSchedule
from quantify_scheduler.json_utils import pathlib
import tqdm
import time
import xarray
from logger.tac_logger import logger
from utilities.status import ClusterStatus
from calibration_schedules.time_of_flight import measure_time_of_flight
from workers.dataset_utils import configure_dataset, handle_ro_freq_optimization, save_dataset
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
colorama_init()


import redis

redis_connection = redis.Redis(decode_responses=True)

def measure_node(
    node,
    compiled_schedule: CompiledSchedule,
    lab_ic,
    data_path: pathlib.Path,
    cluster_status = ClusterStatus.real,
    measurement = (1,1)
    ):

    schedule_duration = compiled_schedule.get_schedule_duration()
    if 'loop_repetitions' in node.node_dictionary:
        schedule_duration *= node.node_dictionary['loop_repetitions']

    measurement_message = ''
    if measurement[1] > 1:
        measurement_message = f'. Measurement {measurement[0]+1} of {measurement[1]}'
    message =  f'{schedule_duration:.2f} sec' + measurement_message
    print(f'schedule_duration = {Fore.CYAN}{Style.BRIGHT}{message}{Style.RESET_ALL}')

    raw_dataset = execute_schedule(compiled_schedule, lab_ic, schedule_duration)

    result_dataset = configure_dataset(raw_dataset, node)
    save_dataset(result_dataset, node, data_path)
    if node.name == 'ro_frequency_optimization':
        result_dataset = handle_ro_freq_optimization(result_dataset, states=[0, 1])
    elif node.name == 'ro_frequency_optimization_gef':
        result_dataset = handle_ro_freq_optimization(result_dataset, states=[0, 1, 2])

    logger.info('Finished measurement')
    return result_dataset

def execute_schedule(
    compiled_schedule: CompiledSchedule,
    lab_ic,
    schedule_duration: float
    ) -> xarray.Dataset:

    logger.info('Starting measurement')
    cluster_status = ClusterStatus.real

    def run_measurement() -> None:
        lab_ic.prepare(compiled_schedule)
        lab_ic.start()
        lab_ic.wait_done(timeout_sec=600)

    def display_progress():
        steps = int(schedule_duration * 5)
        if cluster_status == ClusterStatus.dummy:
            progress_sleep = 0.004
        elif cluster_status == ClusterStatus.real:
            progress_sleep = 0.2
        for _ in tqdm.tqdm(range(steps), desc=compiled_schedule.name, colour='blue'):
            time.sleep(progress_sleep)
    thread_tqdm = threading.Thread(target=display_progress)
    thread_tqdm.start()
    thread_lab = threading.Thread(target=run_measurement)
    thread_lab.start()
    thread_lab.join()
    thread_tqdm.join()

    raw_dataset: xarray.Dataset = lab_ic.retrieve_acquisition()
    lab_ic.stop()
    logger.info('Raw dataset acquired')

    return raw_dataset
