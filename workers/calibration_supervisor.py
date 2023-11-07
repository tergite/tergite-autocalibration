# This code is part of Tergite
import argparse
from utilities.status import DataStatus
from logger.tac_logger import logger
from workers.compilation_worker import precompile
from workers.execution_worker import measure_node
from nodes.node import NodeFactory
from workers.post_processing_worker import post_process
from utilities.status import ClusterStatus
from qblox_instruments import Cluster

from nodes.graph import filtered_topological_order
from utilities.visuals import draw_arrow_chart
from config_files.settings import lokiA_IP
from workers.dummy_setup import dummy_cluster

from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
from utilities.user_input import user_requested_calibration
import toml
import redis
from matplotlib import pyplot as plt
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

bus_list = [ [qubits[i],qubits[i+1]] for i in range(len(qubits)-1) ]
couplers = [bus[0]+'_'+bus[1]for bus in bus_list]

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
        
        for coupler in couplers:
            redis_key = f'couplers:{coupler}'
            calibration_supervisor_key = f'cs:{coupler}'
            for field_key, field_value in node_parameters_dictionary.items():
                # check if field already exists
                if not redis_connection.hexists(redis_key, field_key):
                    redis_connection.hset(f'couplers:{coupler}', field_key, field_value)
            # flag for the calibration supervisor
            if not redis_connection.hexists(calibration_supervisor_key, node):
                redis_connection.hset(f'cs:{coupler}', node, 'not_calibrated' )

        for coupler in couplers:
            redis_key = f'couplers:{coupler}'
            calibration_supervisor_key = f'cs:{coupler}'
            for field_key, field_value in node_parameters_dictionary.items():
                # check if field already exists
                if not redis_connection.hexists(redis_key, field_key):
                    redis_connection.hset(f'couplers:{coupler}', field_key, field_value)
            # flag for the calibration supervisor
            if not redis_connection.hexists(calibration_supervisor_key, node):
                redis_connection.hset(f'cs:{coupler}', node, 'not_calibrated' )

    # Populate the Redis database with the initial 'reasonable' parameter values
    for qubit in qubits:
        for parameter_key, parameter_value in initial_parameters['all'].items():
            redis_connection.hset(f"transmons:{qubit}", parameter_key, parameter_value)

        for parameter_key, parameter_value in initial_parameters[qubit].items():
            redis_connection.hset(f"transmons:{qubit}", parameter_key, parameter_value)

    for coupler in couplers:
        for parameter_key, parameter_value in initial_parameters['all'].items():
            redis_connection.hset(f"couplers:{coupler}", parameter_key, parameter_value)

        # for parameter_key, parameter_value in initial_parameters[coupler].items():
        #     redis_connection.hset(f"couplers:{coupler}", parameter_key, parameter_value)

    for node in topo_order:
        inspect_node(node)
        logger.info(f'{node} node is completed')


def inspect_node(node: str):
    logger.info(f'Inspecting node {node}')
    # breakpoint()
    # Reapply the all initials. This is because of two tones messing with mw_duration
    # TODO: is that necessary?
    initial_parameters = transmon_configuration['initials']
    qubits = user_requested_calibration['all_qubits']
    for qubit in qubits:
        for parameter_key, parameter_value in initial_parameters['all'].items():
            redis_connection.hset(f"transmons:{qubit}", parameter_key, parameter_value)

    for coupler in couplers:
        for parameter_key, parameter_value in initial_parameters['all'].items():
            redis_connection.hset(f"couplers:{coupler}", parameter_key, parameter_value)

    #Populate the Redis database with node specific parameter values
    qubits_statuses = [redis_connection.hget(f"cs:{qubit}", node) == 'calibrated' for qubit in qubits]
    coupler_statuses = [redis_connection.hget(f"cs:{coupler}", node) == 'calibrated' for coupler in couplers]
    #node is calibrated only when all qubits have the node calibrated:
    is_node_calibrated = all(qubits_statuses)
    if node in transmon_configuration and not is_node_calibrated:
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
        print(u' \u2714 ' + f'{Fore.GREEN}{Style.BRIGHT}Node {node} in spec{Style.RESET_ALL}')
        return

    if status == DataStatus.out_of_spec:
        print(u'\u2691\u2691\u2691 ' + f'{Fore.RED}{Style.BRIGHT}Calibration required for Node {node}{Style.RESET_ALL}')
        calibrate_node(node)


def calibrate_node(node_label: str):
    logger.info(f'Calibrating node {node_label}')
    qubits = user_requested_calibration['all_qubits']
    node_dictionary = user_requested_calibration['node_dictionary']

    # Load the latest transmons state onto the job
    device_config = {}
    for qubit in qubits:
        device_config[qubit] = redis_connection.hgetall(f"transmons:{qubit}")
    
    for coupler in couplers:
        device_config[coupler] = redis_connection.hgetall(f"couplers:{coupler}")

    # node = Node(node_label, qubits, node_dictionary)

    node = node_factory.create_node(node_label, qubits, **node_dictionary)

    compiled_schedule = precompile(node)
    result_dataset = measure_node(
        node,
        compiled_schedule,
        clusterA,
        lab_ic,
        cluster_status=args.cluster_status
    )

    logger.info('measurement completed')
    post_process(result_dataset, node,data_path)
    logger.info('analysis completed')


# main
calibrate_system()
