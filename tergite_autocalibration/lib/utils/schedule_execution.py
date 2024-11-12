# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
import threading
import time

import tqdm
import xarray
from colorama import Fore, Style
from quantify_scheduler.instrument_coordinator.instrument_coordinator import (
    CompiledSchedule,
    InstrumentCoordinator,
)

from tergite_autocalibration.utils.logger.tac_logger import logger
from tergite_autocalibration.utils.dto.enums import MeasurementMode


def execute_schedule(
    compiled_schedule: CompiledSchedule,
    schedule_duration: float,
    lab_ic: InstrumentCoordinator,
    cluster_status,
) -> xarray.Dataset:
    logger.info("Starting measurement")

    def run_measurement() -> None:
        lab_ic.prepare(compiled_schedule)
        lab_ic.start()
        lab_ic.wait_done(timeout_sec=3600)

    def display_progress() -> None:
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

    return raw_dataset


def display_duration_information(
    schedule_duration: float, schedule_keywords: dict, measurement: tuple
) -> None:
    if "loop_repetitions" in schedule_keywords:
        schedule_duration *= schedule_keywords["loop_repetitions"]

    measurement_message = ""
    if measurement[1] > 1:
        measurement_message = f". Measurement {measurement[0] + 1} of {measurement[1]}"
    message = f"{schedule_duration:.2f} sec" + measurement_message
    print(f"schedule_duration = {Fore.CYAN}{Style.BRIGHT}{message}{Style.RESET_ALL}")
