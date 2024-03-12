def populate_parking_currents(
    transmon_configuration: dict,
    couplers: list,
    redis_connection
    ):

    initial_device_config = transmon_configuration['initials']

    initial_coupler_parameters = initial_device_config['couplers']

    for coupler in couplers:
        if coupler in initial_coupler_parameters:
            for parameter_key, parameter_value in initial_coupler_parameters[coupler].items():
                redis_connection.hset(f"couplers:{coupler}", parameter_key, parameter_value)


def populate_initial_parameters(
        transmon_configuration: dict,
        qubits: list,
        couplers: list,
        redis_connection
    ):

    initial_device_config = transmon_configuration['initials']

    initial_qubit_parameters = initial_device_config['qubits']
    initial_coupler_parameters = initial_device_config['couplers']

    # Populate the Redis database with the initial 'reasonable'
    # parameter values from the toml file

    for qubit in qubits:
        # parameter common to all qubits:
        for module_key, module_value in initial_qubit_parameters['all'].items():
            print(f'{ module_key = }')
            print(f'{ module_value = }')
            if isinstance(module_value, dict):
                for parameter_key, parameter_value in module_value.items():
                    sub_module_key = module_key + ':' + parameter_key
                    redis_connection.hset(f"transmons:{qubit}", sub_module_key, parameter_value)
            else:
                redis_connection.hset(f"transmons:{qubit}", module_key, module_value)

        # parameter specific to each qubit:
        for module_key, module_value in initial_qubit_parameters[qubit].items():
            if isinstance(module_value, dict):
                for parameter_key, parameter_value in module_value.items():
                    sub_module_key = module_key + ':' + parameter_key
                    redis_connection.hset(f"transmons:{qubit}", sub_module_key, parameter_value)
            else:
                redis_connection.hset(f"transmons:{qubit}", module_key, module_value)

    for coupler in couplers:
        for module_key, module_value in initial_coupler_parameters['all'].items():
            redis_connection.hset(f"couplers:{coupler}", module_key, module_value)

        if coupler in initial_coupler_parameters:
            for module_key, module_value in initial_coupler_parameters[coupler].items():
                redis_connection.hset(f"couplers:{coupler}", module_key, module_value)



def populate_node_parameters(
    node_name: str,
    is_node_calibrated: bool,
    transmon_configuration: dict,
    qubits: list,
    couplers: list,
    redis_connection
    ):
    #Populate the Redis database with node specific parameter values from the toml file
    if node_name in transmon_configuration and not is_node_calibrated:
        node_specific_dict = transmon_configuration[node_name]['all']
        for field_key, field_value in node_specific_dict.items():
            if isinstance(field_value, dict):
                for sub_field_key, sub_field_value in field_value.items():
                    sub_field_key = field_key + ':' + sub_field_key
                    for qubit in qubits:
                        redis_connection.hset(f'transmons:{qubit}', sub_field_key, sub_field_value)
                    for coupler in couplers:
                        redis_connection.hset(f'couplers:{coupler}', sub_field_key, sub_field_value)
            else:
                for qubit in qubits:
                    redis_connection.hset(f'transmons:{qubit}', field_key, field_value)
                for coupler in couplers:
                    redis_connection.hset(f'couplers:{coupler}', field_key, field_value)


def populate_quantities_of_interest(
        transmon_configuration: dict,
        qubits: list,
        couplers: list,
        redis_connection
    ):
    # Populate the Redis database with the quantities of interest, at Nan value
    # Only if the key does NOT already exist
    quantities_of_interest = transmon_configuration['qoi']
    qubit_quantities_of_interest = quantities_of_interest['qubits']
    coupler_quantities_of_interest = quantities_of_interest['couplers']

    for node_name, node_parameters_dictionary in qubit_quantities_of_interest.items():
        # named field as Redis calls them fields
        for qubit in qubits:
            redis_key = f'transmons:{qubit}'
            calibration_supervisor_key = f'cs:{qubit}'
            for field_key, field_value in node_parameters_dictionary.items():
                if isinstance(field_value, dict):
                    for parameter_name, parameter_value in field_value.items():
                        '''
                        e.g. parameter_name -> 'acq_delay'
                             field_key -> 'measure'
                             sub_field_key -> 'measure:acq_delay'
                        '''
                        sub_field_key = field_key + ':' + parameter_name
                        if not redis_connection.hexists(redis_key, sub_field_key):
                            redis_connection.hset(f'transmons:{qubit}', sub_field_key, parameter_value)
                # check if field already exists
                elif not redis_connection.hexists(redis_key, field_key):
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


def reset_all_nodes(
        nodes,
        qubits: list,
        couplers: list,
        redis_connection
    ):
    for qubit in qubits:
        fields =  redis_connection.hgetall(f'transmons:{qubit}').keys()
        key = f'transmons:{qubit}'
        cs_key = f'cs:{qubit}'
        for field in fields:
            redis_connection.hset(key, field, 'nan' )
        for node in nodes:
            redis_connection.hset(cs_key, node, 'not_calibrated' )

    for coupler in couplers:
        fields =  redis_connection.hgetall(f'couplers:{coupler}').keys()
        key = f'couplers:{coupler}'
        cs_key = f'cs:{coupler}'
        for field in fields:
            redis_connection.hset(key, field, 'nan' )
        for node in nodes:
            redis_connection.hset(cs_key, node, 'not_calibrated' )
