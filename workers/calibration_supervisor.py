# This code is part of Tergite
import argparse
from datetime import datetime
import pathlib

from utilities.status import DataStatus
from logger.tac_logger import logger
from workers.compilation_worker import precompile
from workers.execution_worker import measure_node
from nodes.node import NodeFactory
from workers.post_processing_worker import post_process
from utilities.status import ClusterStatus
from qblox_instruments import Cluster
from workers.hardware_utils import SpiDAC
from workers.worker_utils import create_node_data_path

from nodes.graph import filtered_topological_order
from utilities.visuals import draw_arrow_chart
from config_files.settings import lokiA_IP
# from workers.dummy_setup import dummy_cluster

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
# parser.add_argument(
#     '--d', dest='cluster_mode',
#     action='store_const',
#     const=ClusterStatus.dummy, default=ClusterStatus.real
# )
# args = parser.parse_args()
class Args:
    def __init__(self):
        self.cluster_mode = ClusterStatus.real
args = Args()        
args.cluster_mode = ClusterStatus.real
# Settings
transmon_configuration = toml.load('./config_files/device_config.toml')


node_factory = NodeFactory()


def set_module_att(cluster):
    # XY lines
    for idx,module in enumerate(cluster.modules[0:13]):
        if idx in [2,3,8]:
            module.out0_att(12)
        else:
            module.out0_att(16)
        # if idx in [1,6]:
        #     module.out0_att(16)
        # else:
        #     module.out0_att(60)
    print('XY: '+module.name + '_att:'+ str(module.out0_att()) + 'dB')
    # Flux lines
    for module in cluster.modules[0:13]:
        module.out1_att(40)
        # module.out1_att(60)
    print('FL: '+module.name + '_att:'+ str(module.out1_att()) + 'dB')
    # Readout lines
    for module in cluster.modules[15:17]:
        module.out0_att(12)
    print('RO: '+module.name + '_att:'+ str(module.out0_att()) + 'dB')

if args.cluster_mode == ClusterStatus.real:
# if args.cluster_mode == ClusterStatus.real:
    Cluster.close_all()
    clusterA = Cluster("clusterA", lokiA_IP)
    # clusterA.reset()
    set_module_att(clusterA)
    lab_ic = InstrumentCoordinator('lab_ic')
    lab_ic.add_component(ClusterComponent(clusterA))
    lab_ic.timeout(222)

qubits = user_requested_calibration['all_qubits']
couplers = user_requested_calibration['couplers']
# bus_list = [[qubits[i], qubits[i+1]] for i in range(len(qubits) - 1)]
# couplers = [bus[0] + '_' + bus[1] for bus in bus_list]

def redis_init_toml():

    initial_qubit_parameters = transmon_configuration['initials']['qubits']
    initial_coupler_parameters = transmon_configuration['initials']['couplers']

    # Populate the Redis database with the quantities of interest, at Nan value
    # Only if the key does NOT already exist
    qubit_quantities_of_interest = transmon_configuration['qoi']['qubits']
    coupler_quantities_of_interest = transmon_configuration['qoi']['couplers']
    for node_name, node_parameters_dictionary in qubit_quantities_of_interest.items():
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

    for node_name, node_parameters_dictionary in coupler_quantities_of_interest.items():
        for coupler in couplers:
            redis_key = f'couplers:{coupler}'
            calibration_supervisor_key = f'cs:{coupler}'
            for field_key, field_value in node_parameters_dictionary.items():
                # check if field already exists
                if not redis_connection.hexists(redis_key, field_key):
                    redis_connection.hset(f'couplers:{coupler}', field_key, field_value)
            # flag for the calibration supervisor
            if not redis_connection.hexists(calibration_supervisor_key, node_name):
                redis_connection.hset(f'cs:{coupler}', node_name, 'not_calibrated' )


    # Populate the Redis database with the initial 'reasonable'
    # parameter values from the toml file
    for qubit in qubits:
        # parameter common to all qubits:
        for parameter_key, parameter_value in initial_qubit_parameters['all'].items():
            redis_connection.hset(f"transmons:{qubit}", parameter_key, parameter_value)

        # parameter specific to each qubit:
        for parameter_key, parameter_value in initial_qubit_parameters[qubit].items():
            redis_connection.hset(f"transmons:{qubit}", parameter_key, parameter_value)

    for coupler in couplers:
        for parameter_key, parameter_value in initial_coupler_parameters['all'].items():
            redis_connection.hset(f"couplers:{coupler}", parameter_key, parameter_value)

        if coupler in initial_coupler_parameters:
            for parameter_key, parameter_value in initial_coupler_parameters[coupler].items():
                redis_connection.hset(f"couplers:{coupler}", parameter_key, parameter_value)

def write_calibrate_paras(node):
    node_specific_dict = transmon_configuration[node]['all']
    for field_key, field_value in node_specific_dict.items():
        for qubit in qubits:
            redis_connection.hset(f'transmons:{qubit}', field_key, field_value)

def calibrate_system():
    logger.info('Starting System Calibration')
    target_node = user_requested_calibration['target_node']
    topo_order = filtered_topological_order(target_node)
    N_qubits = len(qubits)
    draw_arrow_chart(f'Qubits: {N_qubits}', topo_order)

    redis_init_toml()

    # if target_node == 'cz_chevron':
    #     set_module_att(clusterA)
    #     for coupler in couplers:
    #         spi = SpiDAC()
    #         spi.set_parking_current(coupler)

    for calibration_node in topo_order:
        inspect_node(calibration_node)
        logger.info(f'{calibration_node} node is completed')


def inspect_node(node: str):
    logger.info(f'Inspecting node {node}')

    if node in ['coupler_spectroscopy','cz_chevron','cz_calibration','cz_calibration_ssro','cz_dynamic_phase']:
        coupler_statuses = [redis_connection.hget(f"cs:{coupler}", node) == 'calibrated' for coupler in couplers]
        is_node_calibrated = all(coupler_statuses)
    else:
        qubits_statuses = [redis_connection.hget(f"cs:{qubit}", node) == 'calibrated' for qubit in qubits]
        is_node_calibrated = all(qubits_statuses)

    #Populate the Redis database with node specific parameter values from the toml file
    #node is calibrated only when all qubits have the node calibrated:
    if node in transmon_configuration and not is_node_calibrated:
        write_calibrate_paras(node)
            # If needed add an all couplers initializer here but with a different key e.g. all_couplers

    #Check Redis if node is calibrated
    status = DataStatus.undefined

    if node in ['coupler_spectroscopy','cz_chevron','cz_calibration','cz_calibration_ssro','cz_dynamic_phase']:
        for coupler in couplers:
            # the calibrated, not_calibrated flags may be not necessary,
            # just store the DataStatus on Redis
            is_Calibrated = redis_connection.hget(f"cs:{coupler}", node)
            if is_Calibrated == 'not_calibrated':
                status = DataStatus.out_of_spec
                break  # even if a single qubit is not_calibrated mark as out_of_spec
            elif is_Calibrated == 'calibrated':
                status = DataStatus.in_spec
            else:
                raise ValueError(f'status: {status}')
    else:
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
        print(f' \u2714  {Fore.GREEN}{Style.BRIGHT}Node {node} in spec{Style.RESET_ALL}')
        # print(f'{Fore.GREEN}{Style.BRIGHT} + u" \u2714 " + Node {node} in spec{Style.RESET_ALL}')
        return

    if status == DataStatus.out_of_spec:
        print(u'\u2691\u2691\u2691 ' + f'{Fore.RED}{Style.BRIGHT}Calibration required for Node {node}{Style.RESET_ALL}')
        calibrate_node(node)


def calibrate_node(node_label: str, **static_parameters):
    logger.info(f'Calibrating node {node_label}')
    redis_init_toml()
    if node_label in transmon_configuration:
        write_calibrate_paras(node_label)
    # node_dictionary = user_requested_calibration['node_dictionary']
    if couplers is not None and len(couplers):
        static_parameters["couplers"] = couplers
    bin_mode = static_parameters.pop("bin_mode", None)
    repetitions = static_parameters.pop("repetitions", None)
    node = node_factory.create_node(node_label, qubits, **static_parameters)
    data_path = create_node_data_path(node)

    #TODO precomiple should support support at least two types of samplespace: coarse and fine. 
    compiled_schedule = precompile(node, bin_mode=bin_mode, repetitions=repetitions)
    result_dataset = measure_node(
        node,
        compiled_schedule,
        lab_ic,
        data_path,
        cluster_mode=args.cluster_mode,
    )

    logger.info('measurement completed')
    all_results = post_process(result_dataset, node, data_path=data_path)
    logger.info('analysis completed')
    return [data_path,all_results]


# main
# calibrate_system()
# logger.info('calibration completed, closing cluster')
# clusterA.reset()
# clusterA.close()