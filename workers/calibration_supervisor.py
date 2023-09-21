# This code is part of Tergite
import argparse
from utilities.status import DataStatus
from logger.tac_logger import logger
from workers.compilation_worker import precompile
from workers.execution_worker import measure
from workers.post_processing_worker import post_process
from utilities.status import ClusterStatus
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
colorama_init()

import utilities.user_input as user_input

import toml
import redis

redis_connection = redis.Redis(decode_responses=True)
parser = argparse.ArgumentParser(
        prog='Tergite Automatic Calibration',
        )
parser.add_argument('--d', dest='cluster_status', action='store_const',const=ClusterStatus.dummy,default=ClusterStatus.real)
args = parser.parse_args()

# Settings
transmon_configuration = toml.load('./config_files/device_config.toml')
qubits = user_input.qubits

def calibrate_system():
    logger.info('Starting System Calibration')
    #breakpoint()
    nodes = user_input.nodes
    node_to_be_calibrated = user_input.target_node
    topo_order = nodes[:nodes.index(node_to_be_calibrated) + 1]
    initial_parameters = transmon_configuration['initials']

    #Populate the Redis database with the quantities of interest, at Nan value
    #Only if the key does NOT already exist
    quantities_of_interest = transmon_configuration['qoi']
    for node, node_parameters_dictionary in quantities_of_interest.items():
        # named field as Redis calls them fields
        for qubit in qubits:
            redis_key = f'transmons:{qubit}'
            calibration_supervisor_key = f'cs:{qubit}'
            for field_key, field_value in node_parameters_dictionary.items():
                # check if field already exists
                if not redis_connection.hexists(redis_key, field_key):
                    redis_connection.hset(f'transmons:{qubit}', field_key, field_value)
            # flag for the calibration supervisor
            if not redis_connection.hexists(calibration_supervisor_key, node):
                redis_connection.hset(f'cs:{qubit}', node, 'not_calibrated' )

    #Populate the Redis database with the initial 'reasonable' parameter values
    for qubit in qubits:
        for parameter_key, parameter_value in initial_parameters['all'].items():
            redis_connection.hset(f"transmons:{qubit}", parameter_key, parameter_value)

        for parameter_key, parameter_value in initial_parameters[qubit].items():
            redis_connection.hset(f"transmons:{qubit}", parameter_key, parameter_value)

    for node in topo_order:
        inspect_node(node)
        logger.info(f'{node} node is completed')


def inspect_node(node:str):
    logger.info(f'Inspecting node {node}')
    #breakpoint()
    #Reapply the all initials. This is because of two tones messing with mw_duration
    initial_parameters = transmon_configuration['initials']
    for qubit in qubits:
        for parameter_key, parameter_value in initial_parameters['all'].items():
            redis_connection.hset(f"transmons:{qubit}", parameter_key, parameter_value)

    #Populate the Redis database with node specific parameter values
    qubits_statuses = [redis_connection.hget(f"cs:{qubit}", node) == 'calibrated' for qubit in qubits]
    #node is calibrated only when all qubits have the node calibrated:
    is_node_calibrated = all(qubits_statuses)
    if node in transmon_configuration and not is_node_calibrated:
        node_specific_dict = transmon_configuration[node]['all']
        for field_key, field_value in node_specific_dict.items():
            for qubit in qubits:
                redis_connection.hset(f'transmons:{qubit}', field_key, field_value)

    #Check Redis if node is calibrated
    status = DataStatus.undefined

    for qubit in qubits:
        # the calibrated, not_calibrated flags may be not necessary,
        # just store the DataStatus on Redis
        is_Calibrated = redis_connection.hget(f"cs:{qubit}", node)
        if is_Calibrated == 'not_calibrated':
            status = DataStatus.out_of_spec
            break #even if a single qubit is not_calibrated mark as out_of_spec
        elif is_Calibrated == 'calibrated':
            status = DataStatus.in_spec
        else:
            raise ValueError(f'status: {status}')

    if status == DataStatus.in_spec:
       print(u' \u2705 ' + f'{Fore.GREEN}{Style.BRIGHT}Node {node} in spec{Style.RESET_ALL}')
       # print(u' \u2705 ' + f'Node {node} in spec')
       return

    if status == DataStatus.out_of_spec:
       print(u'\u2691\u2691\u2691 '+ f'{Fore.RED}{Style.BRIGHT}Calibration required for Node {node}{Style.RESET_ALL}')
       # print(u'\u2691\u2691\u2691 '+ f'Calibration required for Node {node}')
       calibrate_node(node)


def calibrate_node(node:str):
    logger.info(f'Calibrating node {node}')
    job = user_input.user_requested_calibration(node)

    # Load the latest transmons state onto the job
    device_config = {}
    for qubit in qubits:
        device_config[qubit] = redis_connection.hgetall(f"transmons:{qubit}")

    job["device_config"] = device_config
    job_id = job["job_id"]

    samplespace = job['experiment_params'][node]
    logger.info(f'Sending to precompile')

    compiled_schedule, schedule_duration = precompile(node, samplespace)
    result_dataset = measure(compiled_schedule, schedule_duration, samplespace, node, cluster_status=args.cluster_status)
    logger.info(f'measurement completed')
    post_process(result_dataset, node)
    logger.info(f'analysis completed')


#main
calibrate_system()
