
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

