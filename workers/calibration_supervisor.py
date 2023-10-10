# This code is part of Tergite
import argparse
from utilities.status import DataStatus
import xarray as xr
from logger.tac_logger import logger
from workers.compilation_worker import precompile
from workers.execution_worker import measure
from nodes.node import node_definitions
from workers.post_processing_worker import post_process
from utilities.status import ClusterStatus
from qcodes import validators
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
import utilities.user_input as user_input
import toml
import redis
from qblox_instruments import SpiRack
from qblox_instruments.qcodes_drivers.spi_rack_modules import S4gModule

colorama_init()

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
       return

    if status == DataStatus.out_of_spec:
       print(u'\u2691\u2691\u2691 '+ f'{Fore.RED}{Style.BRIGHT}Calibration required for Node {node}{Style.RESET_ALL}')
       calibrate_node(node)


def calibrate_node(node_label:str):
    logger.info(f'Calibrating node {node_label}')
    dummy = False
    if args.cluster_status == ClusterStatus.dummy:
        dummy = True
    job = user_input.user_requested_calibration(node_label,dummy)

    # Load the latest transmons state onto the job
    device_config = {}
    for qubit in qubits:
        device_config[qubit] = redis_connection.hgetall(f"transmons:{qubit}")

    samplespace = job['experiment_params'][node_label]

    node = node_definitions[node_label]



    #TODO this is terrible
    compiled_schedules, schedule_durations, partial_samplespaces = precompile(node, qubits, samplespace)
    compilation_zip = list(zip(compiled_schedules, schedule_durations, partial_samplespaces))
    result_dataset = xr.Dataset()
    if node.name == 'coupler_spectroscopy':
        in_prompt = str(input('Run coupler spectroscopy: Y/N ?'))
        assert(in_prompt=='Y')
        spi_mod_number = 4
        spi_mod_name = f'module{spi_mod_number}'
        dac_name = 'dac0'

        spi = SpiRack("loki_rack", "COM99") ###
        spi.add_spi_module(spi_mod_number, "S4g")
        spi.instrument_modules[spi_mod_name][dac_name].ramp_rate(200e-6)
        for dac_name, dac in spi.instrument_modules[spi_mod_name].submodules.items():
            dac.current.vals=validators.Numbers(min_value=-4e-3, max_value=4e-3)

        def set_current(current_value: float):
            spi.instrument_modules[spi_mod_name][dac_name].current(current_value)

        dc_currents = samplespace['dc_currents']
        compiled_schedule = compiled_schedules[0]
        schedule_duration = schedule_durations[0]
        logger.info('Starting coupler spectroscopy')
        for current in dc_currents:
            set_current(current)
            dataset = measure(
                compiled_schedule,
                schedule_duration,
                samplespace,
                node.name,
                #[compilation_indx, len(list(compilation_zip))],
                cluster_status=args.cluster_status
            )
            dataset = xr.merge([result_dataset,dataset])
        spi.instrument_modules[spi_mod_name].set_dacs_zero()
    else:
        for compilation_indx, compilation in enumerate(compilation_zip):
            compiled_schedule, schedule_duration, samplespace = compilation
            dataset = measure(
                compiled_schedule,
                schedule_duration,
                samplespace,
                node.name,
                #[compilation_indx, len(list(compilation_zip))],
                cluster_status=args.cluster_status
            )
            if compilation_indx == 0:
                result_dataset = dataset
            else:
                for var in result_dataset.data_vars:
                    coords = result_dataset[var].coords
                    for coord in coords:
                        if 'qubit_state' not in coord:
                            concat_coord = coord
                            break

                    #breakpoint()
                    darray = xr.concat([result_dataset[var], dataset[var]], dim=concat_coord)
                    result_dataset = result_dataset.drop_vars(var)
                    result_dataset = result_dataset.drop_dims(concat_coord)
                    result_dataset[var] = darray

    logger.info('measurement completed')
    post_process(result_dataset, node)
    logger.info('analysis completed')

#main
calibrate_system()
