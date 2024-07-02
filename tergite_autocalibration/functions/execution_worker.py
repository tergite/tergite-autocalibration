"""Retrieve the compiled schedule and run it"""
import threading
import time

from colorama import Fore
from colorama import Style
from colorama import init as colorama_init
from quantify_scheduler.instrument_coordinator.instrument_coordinator import (
    CompiledSchedule,
)
from quantify_scheduler.json_utils import pathlib
import tqdm
import xarray

from tergite_autocalibration.utils.dataset_utils import (
    configure_dataset,
    retrieve_dummy_dataset,
    save_dataset,
)  # , handle_ro_freq_optimization
from tergite_autocalibration.utils.logger.tac_logger import logger
from tergite_autocalibration.utils.enums import MeasurementMode

colorama_init()


def measure_node(
    node,
    compiled_schedule: CompiledSchedule,
    lab_ic,
    data_path: pathlib.Path,
    cluster_status=MeasurementMode.real,
    measurement=(1, 1),
):
    # TODO: This function should be move to the node
    schedule_duration = compiled_schedule.get_schedule_duration()
    if "loop_repetitions" in node.schedule_keywords:
        schedule_duration *= node.schedule_keywords["loop_repetitions"]

    measurement_message = ""
    if measurement[1] > 1:
        measurement_message = f". Measurement {measurement[0] + 1} of {measurement[1]}"
    message = f"{schedule_duration:.2f} sec" + measurement_message
    print(f"schedule_duration = {Fore.CYAN}{Style.BRIGHT}{message}{Style.RESET_ALL}")

    raw_dataset = execute_schedule(
        compiled_schedule, lab_ic, schedule_duration, cluster_status
    )

    if cluster_status == MeasurementMode.real:
        result_dataset = configure_dataset(raw_dataset, node)
        save_dataset(result_dataset, node, data_path)
    else:
        result_dataset = retrieve_dummy_dataset(node)

    logger.info("Finished measurement")
    return result_dataset


def execute_schedule(
    compiled_schedule: CompiledSchedule,
    lab_ic,
    schedule_duration: float,
    cluster_status,
) -> xarray.Dataset:

    logger.info("Starting measurement")

    def run_measurement() -> None:
        lab_ic.prepare(compiled_schedule)
        lab_ic.start()
        lab_ic.wait_done(timeout_sec=3600)

    def display_progress():
        steps = int(schedule_duration * 5)
        if cluster_status == MeasurementMode.dummy:
            progress_sleep = 0.004
        elif cluster_status == MeasurementMode.real:
            progress_sleep = 0.2
        for _ in tqdm.tqdm(range(steps), desc=compiled_schedule.name, colour="blue"):
            time.sleep(progress_sleep)

    thread_tqdm = threading.Thread(target=display_progress)
    thread_tqdm.start()
    thread_lab = threading.Thread(target=run_measurement)
    thread_lab.start()
    thread_lab.join()
    thread_tqdm.join()

    raw_dataset: xarray.Dataset = lab_ic.retrieve_acquisition()
    lab_ic.stop()
    logger.info("Raw dataset acquired")

    return raw_dataset
