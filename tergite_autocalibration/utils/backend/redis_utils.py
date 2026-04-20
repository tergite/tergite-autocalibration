# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024, 2025, 2026
# (c) Copyright Stefan Hill 2024
# (C) Copyright Michele Faucci Giannelli 2025
# (C) Copyright Abdullah Al Amin 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import toml

from tergite_autocalibration.config.globals import CONFIG, REDIS_CONNECTION
from tergite_autocalibration.lib.base.node import CouplerNode, QubitNode
from tergite_autocalibration.lib.utils.node_factory import NodeFactory
from tergite_autocalibration.utils.logging import logger


def populate_initial_parameters(qubits: list, couplers: list, redis_connection):
    initial_qubit_parameters = CONFIG.device.qubits
    initial_coupler_parameters = CONFIG.device.couplers

    # Populate the Redis database with the initial 'reasonable'
    # parameter values from the toml file

    for qubit in qubits:
        # parameter common to all qubits:
        if "all" in initial_qubit_parameters.keys():
            for module_key, module_value in initial_qubit_parameters["all"].items():
                if isinstance(module_value, dict):
                    for parameter_key, parameter_value in module_value.items():
                        sub_module_key = module_key + ":" + parameter_key
                        redis_connection.hset(
                            f"transmons:{qubit}", sub_module_key, parameter_value
                        )
                else:
                    redis_connection.hset(
                        f"transmons:{qubit}", module_key, module_value
                    )

        # parameter specific to each qubit:
        for module_key, module_value in initial_qubit_parameters[qubit].items():
            if isinstance(module_value, dict):
                for parameter_key, parameter_value in module_value.items():
                    sub_module_key = module_key + ":" + parameter_key
                    redis_connection.hset(
                        f"transmons:{qubit}", sub_module_key, parameter_value
                    )
            else:
                redis_connection.hset(f"transmons:{qubit}", module_key, module_value)

    for coupler in couplers:
        if "all" in initial_coupler_parameters.keys():
            for module_key, module_value in initial_coupler_parameters["all"].items():
                redis_connection.hset(f"couplers:{coupler}", module_key, module_value)

        if coupler in initial_coupler_parameters:
            for module_key, module_value in initial_coupler_parameters[coupler].items():
                redis_connection.hset(f"couplers:{coupler}", module_key, module_value)


def populate_parking_currents(couplers: list, redis_connection):
    initial_coupler_parameters = CONFIG.device.couplers
    for coupler in couplers:
        if coupler in initial_coupler_parameters:
            for module_key, module_value in initial_coupler_parameters[coupler].items():
                redis_connection.hset(f"couplers:{coupler}", module_key, module_value)


def _qubit_fields_to_redis(qubits: list[str], key: str, value: str, redis_connection):
    for qubit in qubits:
        redis_connection.hset(f"transmons:{qubit}", key, value)


def _coupler_fields_to_redis(
    couplers: list[str], key: str, value: str, redis_connection
):
    for coupler in couplers:
        redis_connection.hset(f"transmons:{coupler}", key, value)


def populate_node_parameters(
    node_name: str,
    is_node_calibrated: bool,
    qubits: list,
    couplers: list,
    redis_connection,
):
    # Populate the Redis database with node specific parameter values from the toml file
    transmon_configuration = toml.load(CONFIG.node)
    if not node_name in transmon_configuration:
        logger.status(f"{node_name} does not have specific node config")
        return
    if is_node_calibrated:
        logger.status(f"{node_name} is already calibrated")
        return
    node_specific_dict = transmon_configuration[node_name].get("all", {})

    for field_key, field_value in node_specific_dict.items():
        if isinstance(field_value, dict):
            for sub_field_key, sub_field_value in field_value.items():
                sub_field_key = field_key + ":" + sub_field_key
                _qubit_fields_to_redis(
                    qubits, sub_field_key, sub_field_value, redis_connection
                )
                _coupler_fields_to_redis(
                    couplers, sub_field_key, sub_field_value, redis_connection
                )
        else:
            _qubit_fields_to_redis(qubits, field_key, field_value, redis_connection)
            _coupler_fields_to_redis(couplers, field_key, field_value, redis_connection)

    # node config for specific couplers:
    for coupler in couplers:
        if coupler in transmon_configuration[node_name]:
            coupler_specific_config = transmon_configuration[node_name][coupler]
            for field_key, field_value in coupler_specific_config.items():
                redis_connection.hset(f"couplers:{coupler}", field_key, field_value)


def revert_node_parameters(node_name: str, qubits: list, redis_connection):

    node_configuration = toml.load(CONFIG.node)
    if not node_name in node_configuration:
        return  # no node specific config found

    initial_qubit_parameters = CONFIG.device.qubits

    node_specific_dict = node_configuration[node_name].get("all", {})

    for field_key, field_value in node_specific_dict.items():
        if not isinstance(field_value, dict):
            raise NotImplementedError("Only field modules supported")
        for sub_field_key in field_value.keys():
            for qubit in qubits:
                initial_qubit_field = initial_qubit_parameters[qubit][field_key]
                initial_value = initial_qubit_field[sub_field_key]
                key = field_key + ":" + sub_field_key
                # restore initial parameter value
                redis_connection.hset(f"transmons:{qubit}", key, initial_value)


def populate_quantities_of_interest(
    node_name: str,
    node_factory: "NodeFactory",
    qubits: list[str],
    couplers: list[str],
    redis_connection,
):
    # Populate the Redis database with the quantities of interest, at Nan value
    # Only if the key does NOT already exist
    # Thuis code should be moved to the specific classes
    node = node_factory.get_node_class(node_name)
    if issubclass(node, QubitNode):
        qubit_qois = node.qubit_qois
        if qubit_qois is None:
            logger.warning(f"No qois for node {node_name}")
            return
        for qubit in qubits:
            redis_key = f"transmons:{qubit}"
            calibration_supervisor_key = f"cs:{qubit}"
            for qoi in qubit_qois:
                if not redis_connection.hexists(redis_key, qoi):
                    redis_connection.hset(f"transmons:{qubit}", qoi, "nan")
                    if qoi == "measure_3state_opt:pulse_amp":
                        redis_connection.hset(f"transmons:{qubit}", qoi, "0")
                    elif qoi == "measure_2state_opt:pulse_amp":
                        redis_connection.hset(f"transmons:{qubit}", qoi, "0")
                    elif qoi == "rxy:motzoi":
                        redis_connection.hset(f"transmons:{qubit}", qoi, "0")
                    elif qoi == "r12:ef_motzoi":
                        redis_connection.hset(f"transmons:{qubit}", qoi, "0")
            # flag for the calibration supervisor
            if not redis_connection.hexists(calibration_supervisor_key, node_name):
                redis_connection.hset(f"cs:{qubit}", node_name, "not_calibrated")

    elif issubclass(node, CouplerNode):
        coupler_qois = node.coupler_qois
        if coupler_qois is not None:
            for coupler in couplers:
                redis_key = f"couplers:{coupler}"
                calibration_supervisor_key = f"cs:{coupler}"
                for qoi in coupler_qois:
                    # check if field already exists
                    if not redis_connection.hexists(redis_key, qoi):
                        redis_connection.hset(f"couplers:{coupler}", qoi, "nan")
                # flag for the calibration supervisor
                if not redis_connection.hexists(calibration_supervisor_key, node_name):
                    redis_connection.hset(f"cs:{coupler}", node_name, "not_calibrated")

    else:
        raise ValueError(
            f"Node {node_name} with base type {node} is not a valid Qubit or Coupler node. Cannot populate quantities of interest."
        )


def fetch_redis_params(param: str, this_element: str):
    if "_" in this_element:
        name = "couplers"
    else:
        name = "transmons"
    redis_config = REDIS_CONNECTION.hgetall(f"{name}:{this_element}")
    return float(redis_config[param])
