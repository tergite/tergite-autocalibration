'''Retrieve the compiled schedule and run it'''
import threading
import time

import tqdm
import xarray
from colorama import Fore
from colorama import Style
from colorama import init as colorama_init
from quantify_scheduler.instrument_coordinator.instrument_coordinator import CompiledSchedule
from quantify_scheduler.json_utils import pathlib

from tergite_autocalibration.utils.dataset_utils import configure_dataset, handle_ro_freq_optimization, save_dataset
from tergite_autocalibration.utils.logger.tac_logger import logger
from tergite_autocalibration.utils.enums import ClusterMode

colorama_init()


def measure_node(
        node,
        compiled_schedule: CompiledSchedule,
        lab_ic,
        data_path: pathlib.Path,
        cluster_mode=ClusterMode.real,
        measurement=(1, 1)
):
    # TODO: This function should be move to the node

    schedule_duration = compiled_schedule.get_schedule_duration()
    if 'loop_repetitions' in node.node_dictionary:
        schedule_duration *= node.node_dictionary['loop_repetitions']

    measurement_message = ''
    if measurement[1] > 1:
        measurement_message = f'. Measurement {measurement[0] + 1} of {measurement[1]}'
    message = f'{schedule_duration:.2f} sec' + measurement_message
    print(f'schedule_duration = {Fore.CYAN}{Style.BRIGHT}{message}{Style.RESET_ALL}')

    raw_dataset = execute_schedule(compiled_schedule, lab_ic, schedule_duration)

    result_dataset = configure_dataset(raw_dataset, node)
    save_dataset(result_dataset, node, data_path)
    if node.name == 'ro_frequency_two_state_optimization':
        result_dataset = handle_ro_freq_optimization(result_dataset, states=[0, 1])
    elif node.name == 'ro_frequency_three_state_optimization':
        result_dataset = handle_ro_freq_optimization(result_dataset, states=[0, 1, 2])

    logger.info('Finished measurement')
    return result_dataset


def execute_schedule(
        compiled_schedule: CompiledSchedule,
        lab_ic,
        schedule_duration: float
) -> xarray.Dataset:
    # TODO: This should go to the BaseMeasurement
    # TODO: The instrument coordinator could be an attribute of the node
    logger.info('Starting measurement')
    cluster_mode = ClusterMode.real

    def run_measurement() -> None:
        lab_ic.prepare(compiled_schedule)
        lab_ic.start()
        lab_ic.wait_done(timeout_sec=3600)

    def display_progress():
        steps = int(schedule_duration * 5)
        if cluster_mode == ClusterMode.dummy:
            progress_sleep = 0.004
        elif cluster_mode == ClusterMode.real:
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
