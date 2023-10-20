'''Retrieve the compiled schedule and run it'''
from quantify_scheduler.instrument_coordinator.instrument_coordinator import CompiledSchedule
from qblox_instruments import SpiRack
from qblox_instruments.qcodes_drivers.spi_rack_modules import S4gModule
from qcodes import validators
from logger.tac_logger import logger
import xarray
from utilities.status import ClusterStatus
from workers.worker_utils import configure_dataset, handle_ro_freq_optimization, to_real_dataset
import threading
import time
import tqdm
from utilities.root_path import data_directory
from calibration_schedules.time_of_flight import measure_time_of_flight
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


def execute_schedule(
        compiled_schedule: CompiledSchedule,
        clusterA,
        lab_ic,
) -> xarray.Dataset:

    logger.info('Starting measurement')
    cluster_status = ClusterStatus.real
    schedule_duration = compiled_schedule.get_schedule_duration()

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
            sleep(progress_sleep)
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


def save_dataset(result_dataset, node):
    measurement_date = datetime.now()
    measurements_today = measurement_date.date().strftime('%Y%m%d')
    time_id = measurement_date.strftime('%Y%m%d-%H%M%S-%f')[:19]
    measurement_id = time_id + '-' + str(uuid4())[:6] + f'-{node.name}'
    data_path = pathlib.Path(data_directory / measurements_today / measurement_id)
    data_path.mkdir(parents=True, exist_ok=True)
    result_dataset = result_dataset.assign_attrs({'name': node.name, 'tuid': measurement_id})
    result_dataset_real = to_real_dataset(result_dataset)
    # to_netcdf doesn't like complex numbers, convert to real/imag to save:
    result_dataset_real.to_netcdf(data_path / 'dataset.hdf5')


class MeasurementFactory:
    #def __init__(self, node):
        #self.node = node

    def select(self, node):
        if node.name in ['coupler_spectroscopy']:
            return CoupledQubitsMeasurement(node)
        else:
            return SingleQubitsMeasurement(node)


class SingleQubitsMeasurement:
    def __init__(self, node):
        self.node = node

    def measure(self, node, compiled_schedule, cluster, ic):
        samplespace = node.samplespace
        raw_dataset = execute_schedule(compiled_schedule, cluster, ic)
        result_dataset = configure_dataset(raw_dataset, samplespace)
        save_dataset(result_dataset, node)
        if node.name == 'ro_frequency_optimization':
            result_dataset = handle_ro_freq_optimization(result_dataset, states=[0, 1])
        elif node.name == 'ro_frequency_optimization_gef':
            result_dataset = handle_ro_freq_optimization(result_dataset, states=[0, 1, 2])
        return result_dataset


class CoupledQubitsMeasurement:
    # coupler sweeps need special treatment. For separate them in their own class

    def __init__(self, node):
        self.node = node
        self.dac = self.create_dac(self.node)
        self.dc_currents = self.node.spi_samplespace['dc_currents'][self.node.coupler]

    def create_dac(self, node):
        coupler_spi_map = {
            'q21q22': (4, 'dac0'),
            'q20q25': (3, 'dac3'),
            'q24q25': (3, 'dac2'),
        }
        coupler = node.coupler
        spi_mod_number, dac_name = coupler_spi_map[coupler]
        spi_mod_name = f'module{spi_mod_number}'
        spi = SpiRack('loki_rack', '/dev/ttyACM0')
        spi.add_spi_module(spi_mod_number, S4gModule)
        this_dac = spi.instrument_modules[spi_mod_name].instrument_modules[dac_name]
        this_dac.ramping_enabled(True)
        this_dac.ramp_rate(500e-6)
        this_dac.ramp_max_step(250e-6)
        this_dac.current.vals = validators.Numbers(min_value=-3e-3, max_value=3e-3)
        # for dac in spi.instrument_modules[spi_mod_name].submodules.values():
        # dac.current.vals = validators.Numbers(min_value=-2e-3, max_value=2e-3)
        return this_dac

    def set_current(self, current_value: float):
        print(f'{ current_value = }')
        print(f'{ self.dac.current() = }')
        self.dac.current(current_value)
        while self.dac.is_ramping():
            print(f'ramping {self.dac.current()}')
            time.sleep(1)
        print('Finished ramping')

    logger.info('Starting coupler spectroscopy')

    def measure(self, node, compiled_schedule, cluster, ic):
        for indx, current in enumerate(self.dc_currents):
            self.set_current(current)

            raw_dataset = execute_schedule(compiled_schedule, cluster, ic)
            dataset = configure_dataset(raw_dataset, node.samplespace)

            dataset = dataset.expand_dims(dim='dc_currents')
            dataset['dc_currents'] = [current]

            if indx == 0:
                result_dataset = dataset
            else:
                result_dataset = xarray.concat([result_dataset, dataset], dim='dc_currents')

        save_dataset(result_dataset, node)
        # TODO verify this
        self.set_current(0)
        return result_dataset


def measure_node(
    node,
    compiled_schedule: CompiledSchedule,
    cluster,
    lab_ic,
    cluster_status=ClusterStatus.real
):

    # the factory determines if the measurement is on single qubits or a coupler is involved
    factory = MeasurementFactory()
    measurement = factory.select(node)
    result_dataset = measurement.measure(node, compiled_schedule, cluster, lab_ic)

    logger.info('Finished measurement')

    return result_dataset
