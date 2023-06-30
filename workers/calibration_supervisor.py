# This code is part of Tergite

from time import sleep
from rq import Queue
from utilities.status import DataStatus
from logger.tac_logger import logger
from workers.compilation_worker import precompile, test

import utilities.user_input as user_input

import toml
import redis

logger.info('Initialize')

# redis_connection = redis.Redis('localhost',6379,decode_responses=True)
redis_connection = redis.Redis(decode_responses=True)
rq_supervisor = Queue(
        'calibration_supervisor', connection=redis_connection
        )


# Settings
transmon_configuration = toml.load('./transmons_config.toml')
qubits = user_input.qubits

def calibrate_system():
    logger.info('Starting System Calibration')
    nodes = user_input.nodes
    node_to_be_calibrated = user_input.node_to_be_calibrated
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


def inspect_node(node:str):
    logger.info(f'Inspecting node {node}')

    #Populate the Redis database with node specific parameter values
    if node in transmon_configuration:
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
       print(u' \u2705 ' + f'Node {node} in spec')
       return

    if status == DataStatus.out_of_spec:
       print(u'\u2691\u2691\u2691 '+ f'Calibration required for Node {node}')
       calibrate_node(node)
       return


def calibrate_node(node:str):
    logger.info(f'Calibrating node {node}')
    job = user_input.user_requested_calibration(node)

    # Load the latest transmons state onto the job
    device_config = {}
    for qubit in qubits:
        device_config[qubit] = redis_connection.hgetall(f"transmons:{qubit}")

    job["device_config"] = device_config
    job_id = job["job_id"]
    #TODO this not a proper way to extract the samplespace
    samplespace = list(job['experiment_params'][node].values())[0]
    # breakpoint()

    rq_supervisor.enqueue(precompile, args=(node, samplespace))
    # rq_supervisor.enqueue(test, args=('hej',))



calibrate_system()
sleep(100)
print('EXITING MAIN')

