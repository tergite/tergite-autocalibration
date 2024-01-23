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
