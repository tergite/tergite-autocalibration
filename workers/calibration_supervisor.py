# This code is part of Tergite
import argparse
from datetime import datetime
import pathlib
import time

from qcodes import validators
from utilities.status import DataStatus
from logger.tac_logger import logger
from workers.compilation_worker import precompile
from workers.execution_worker import measure_node
from nodes.node import NodeFactory
from workers.post_processing_worker import post_process
from utilities.status import ClusterStatus
from qblox_instruments import Cluster, SpiRack
from qblox_instruments.qcodes_drivers.spi_rack_modules import S4gModule

from nodes.graph import filtered_topological_order
from utilities.visuals import draw_arrow_chart
from config_files.settings import lokiA_IP
from workers.dummy_setup import dummy_cluster

from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
from utilities.user_input import user_requested_calibration
from utilities.root_path import data_directory
import toml
import redis
from quantify_scheduler.instrument_coordinator import InstrumentCoordinator
from quantify_scheduler.instrument_coordinator.components.qblox import ClusterComponent

colorama_init()


redis_connection = redis.Redis(decode_responses=True)
parser = argparse.ArgumentParser(prog='Tergite Automatic Calibration',)
parser.add_argument(
    '--d', dest='cluster_status',
    action='store_const',
    const=ClusterStatus.dummy, default=ClusterStatus.real
)
args = parser.parse_args()
# Settings
transmon_configuration = toml.load('./config_files/device_config.toml')


def set_parking_current(coupler: str) -> None:
    coupler_spi_map = {
        'q16_q17': (1, 'dac0'), # slightly heating?
        'q17_q18': (1, 'dac1'),
        'q18_q19': (1, 'dac2'),
        'q19_q20': (1, 'dac3'), # slightly heating
        'q16_q21': (2, 'dac2'),
        'q17_q22': (2, 'dac1'),
        'q18_q23': (2, 'dac0'),
        'q21_q22': (3, 'dac1'),
        'q22_q23': (3, 'dac2'), # badly heating?
        'q23_q24': (3, 'dac3'),
        'q20_q25': (3, 'dac0'),
        'q24_q25': (4, 'dac0'),
    }

    if redis_connection.hexists(f'couplers:{coupler}', 'parking_current'):
        parking_current = redis_connection.hget(f'couplers:{coupler}', 'parking_current')
    else:
        raise ValueError('parking current is not present on redis')

    dc_current_step = 25e-6
    spi_mod_number, dac_name = coupler_spi_map[coupler]
    spi_mod_name = f'module{spi_mod_number}'
    spi = SpiRack('loki_rack', '/dev/ttyACM0')
    spi.add_spi_module(spi_mod_number, S4gModule)
    dac = spi.instrument_modules[spi_mod_name].instrument_modules[dac_name]
    dac.ramping_enabled(False)
    dac.span('range_min_bi')
    dac.current(0)
    dac.ramping_enabled(True)
    dac.ramp_rate(100e-6)
    dac.ramp_max_step(dc_current_step)
    dac.current.vals = validators.Numbers(min_value=-3e-3, max_value=3e-3)
    dac.current(parking_current)
    while dac.is_ramping():
        print(f'ramping {dac.current()}')
        time.sleep(1)
    print('Finished ramping')
    return


node_factory = NodeFactory()


if args.cluster_status == ClusterStatus.real:
    Cluster.close_all()
    clusterA = Cluster("clusterA", lokiA_IP)
    lab_ic = InstrumentCoordinator('lab_ic')
    lab_ic.add_component(ClusterComponent(clusterA))
    lab_ic.timeout(222)

qubits = user_requested_calibration['all_qubits']
bus_list = [[qubits[i], qubits[i+1]] for i in range(len(qubits) - 1)]
couplers = [bus[0] + '_' + bus[1] for bus in bus_list]

def calibrate_system():
    logger.info('Starting System Calibration')
    target_node = user_requested_calibration['target_node']
    topo_order = filtered_topological_order(target_node)
    N_qubits = len(qubits)
    draw_arrow_chart(f'Qubits: {N_qubits}', topo_order)
    initial_parameters = transmon_configuration['initials']

    # Populate the Redis database with the quantities of interest, at Nan value
    # Only if the key does NOT already exist
    quantities_of_interest = transmon_configuration['qoi']
    for node_name, node_parameters_dictionary in quantities_of_interest.items():
        # named field as Redis calls them fields
        for qubit in qubits:
            redis_key = f'transmons:{qubit}'
            calibration_supervisor_key = f'cs:{qubit}'
            for field_key, field_value in node_parameters_dictionary.items():
                # check if field already exists
                if not redis_connection.hexists(redis_key, field_key):
                    redis_connection.hset(f'transmons:{qubit}', field_key, field_value)
            # flag for the calibration supervisor
            if not redis_connection.hexists(calibration_supervisor_key, node_name):
                redis_connection.hset(f'cs:{qubit}', node_name, 'not_calibrated' )


    # Populate the Redis database with the initial 'reasonable'
    # parameter values from the toml file
    for qubit in qubits:
        # parameter common to all qubits:
        for parameter_key, parameter_value in initial_parameters['all'].items():
            redis_connection.hset(f"transmons:{qubit}", parameter_key, parameter_value)

        # parameter specific to each qubit:
        for parameter_key, parameter_value in initial_parameters[qubit].items():
            redis_connection.hset(f"transmons:{qubit}", parameter_key, parameter_value)

    for coupler in couplers:
        for parameter_key, parameter_value in initial_parameters['all'].items():
            redis_connection.hset(f"couplers:{coupler}", parameter_key, parameter_value)

        if coupler in initial_parameters:
            for parameter_key, parameter_value in initial_parameters[coupler].items():
                redis_connection.hset(f"couplers:{coupler}", parameter_key, parameter_value)


    if target_node == 'cz_chevron':
        # when perform 2qubit gates all calibrations are done with the coupler biased
        if 'node_dictionary' in user_requested_calibration:
            node_dictionary = user_requested_calibration['node_dictionary']
            if 'coupled_qubits' in node_dictionary:
                coupled_qubits = node_dictionary['coupled_qubits']
                coupler = coupled_qubits[0] + '_' + coupled_qubits[1]
            else:
                raise ValueError('Misformated user input')
        else:
            raise ValueError('Misformated user input')
        set_parking_current(coupler)

    for calibration_node in topo_order:
        inspect_node(calibration_node)
        logger.info(f'{calibration_node} node is completed')


def inspect_node(node: str):
    logger.info(f'Inspecting node {node}')

    #Populate the Redis database with node specific parameter values from the toml file
    qubits_statuses = [redis_connection.hget(f"cs:{qubit}", node) == 'calibrated' for qubit in qubits]
    # coupler_statuses = [redis_connection.hget(f"cs:{coupler}", node) == 'calibrated' for coupler in couplers]
    #node is calibrated only when all qubits have the node calibrated:
    is_node_calibrated = all(qubits_statuses)
    if node in transmon_configuration and not is_node_calibrated:
        print(f'{ transmon_configuration[node] = }')
        node_specific_dict = transmon_configuration[node]['all']
        for field_key, field_value in node_specific_dict.items():
            for qubit in qubits:
                redis_connection.hset(f'transmons:{qubit}', field_key, field_value)

            for coupler in couplers:
                redis_connection.hset(f'couplers:{coupler}', field_key, field_value)

    #Check Redis if node is calibrated
    status = DataStatus.undefined

    for qubit in qubits:
        # the calibrated, not_calibrated flags may be not necessary,
        # just store the DataStatus on Redis
        is_Calibrated = redis_connection.hget(f"cs:{qubit}", node)
        if is_Calibrated == 'not_calibrated':
            status = DataStatus.out_of_spec
            break  # even if a single qubit is not_calibrated mark as out_of_spec
        elif is_Calibrated == 'calibrated':
            status = DataStatus.in_spec
        else:
            raise ValueError(f'status: {status}')

    if status == DataStatus.in_spec:
        print(u'\u2714 ' + f'{Fore.GREEN}{Style.BRIGHT}Node {node} in spec{Style.RESET_ALL}')
        return

    if status == DataStatus.out_of_spec:
        print(u'\u2691\u2691\u2691 ' + f'{Fore.RED}{Style.BRIGHT}Calibration required for Node {node}{Style.RESET_ALL}')
        calibrate_node(node)


def calibrate_node(node_label: str):
    logger.info(f'Calibrating node {node_label}')
    qubits = user_requested_calibration['all_qubits']
    node_dictionary = user_requested_calibration['node_dictionary']

    node = node_factory.create_node(node_label, qubits, **node_dictionary)

    compiled_schedule = precompile(node)
    result_dataset = measure_node(
        node,
        compiled_schedule,
        lab_ic,
        cluster_status=args.cluster_status
    )

    measurement_date = datetime.now()
    plots_today = measurement_date.date().strftime('%Y%m%d')
    time_id = measurement_date.strftime('%Y%m%d-%H%M%S-%f')[:19]
    measurement_id = time_id + '-' + f'{node.name}'
    data_path = pathlib.Path(data_directory / plots_today / measurement_id)
    data_path.mkdir(parents=True, exist_ok=True)

    logger.info('measurement completed')
    post_process(result_dataset, node, data_path=data_path)
    logger.info('analysis completed')


# main
calibrate_system()
