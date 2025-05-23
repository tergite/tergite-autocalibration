# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (c) Copyright Stefan Hill 2024
# (C) Copyright Michele Faucci Giannelli 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import toml

from tergite_autocalibration.config.globals import REDIS_CONNECTION, CONFIG
from tergite_autocalibration.lib.base.node import CouplerNode, QubitNode
from tergite_autocalibration.lib.utils.node_factory import NodeFactory
from tergite_autocalibration.utils.logging import logger
from tergite_autocalibration.config.legacy import dh
from tergite_autocalibration.tools.mss.convert import structured_redis_storage


def populate_parking_currents(
    transmon_configuration: dict, couplers: list, redis_connection
):
    initial_device_config = transmon_configuration["initials"]

    initial_coupler_parameters = initial_device_config["couplers"]

    for coupler in couplers:
        if coupler in initial_coupler_parameters:
            for parameter_key, parameter_value in initial_coupler_parameters[
                coupler
            ].items():
                redis_connection.hset(
                    f"couplers:{coupler}", parameter_key, parameter_value
                )
                structured_redis_storage(parameter_key, coupler, parameter_value)


def populate_initial_parameters(qubits: list, couplers: list, redis_connection):
    # TODO: This way of loading the device configuration is very simple.
    #       Making it more robust would require some more engineering on the data handler.
    initial_device_config = dh.device

    initial_qubit_parameters = initial_device_config["qubit"]
    initial_coupler_parameters = initial_device_config["coupler"]

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
                        structured_redis_storage(
                            sub_module_key, qubit.strip("q"), parameter_value
                        )
                else:
                    redis_connection.hset(
                        f"transmons:{qubit}", module_key, module_value
                    )
                    structured_redis_storage(module_key, qubit.strip("q"), module_value)

        # parameter specific to each qubit:
        for module_key, module_value in initial_qubit_parameters[qubit].items():
            if isinstance(module_value, dict):
                for parameter_key, parameter_value in module_value.items():
                    sub_module_key = module_key + ":" + parameter_key
                    redis_connection.hset(
                        f"transmons:{qubit}", sub_module_key, parameter_value
                    )
                    structured_redis_storage(
                        sub_module_key, qubit.strip("q"), parameter_value
                    )
            else:
                redis_connection.hset(f"transmons:{qubit}", module_key, module_value)
                structured_redis_storage(module_key, qubit.strip("q"), module_value)

    for coupler in couplers:
        if "all" in initial_coupler_parameters.keys():
            for module_key, module_value in initial_coupler_parameters["all"].items():
                redis_connection.hset(f"couplers:{coupler}", module_key, module_value)
                structured_redis_storage(module_key, coupler, module_value)

        if coupler in initial_coupler_parameters:
            for module_key, module_value in initial_coupler_parameters[coupler].items():
                redis_connection.hset(f"couplers:{coupler}", module_key, module_value)
                structured_redis_storage(module_key, coupler, module_value)


def populate_active_reset_parameters(
    active_reset_configuration: dict, qubits: list, redis_connection
):
    active_reset_device_config = active_reset_configuration["active_reset"]

    ar_qubit_parameters = active_reset_device_config["qubits"]
    logger.info("Populating Active Reset")

    # Populate the Redis database with the initial active reset
    # parameter values from the toml file
    for qubit in qubits:
        # parameter specific to each qubit:
        for module_key, module_value in ar_qubit_parameters[qubit].items():
            if isinstance(module_value, dict):
                for parameter_key, parameter_value in module_value.items():
                    sub_module_key = module_key + ":" + parameter_key
                    redis_connection.hset(
                        f"transmons:{qubit}", sub_module_key, parameter_value
                    )
                    structured_redis_storage(
                        sub_module_key, qubit.strip("q"), parameter_value
                    )
            else:
                redis_connection.hset(f"transmons:{qubit}", module_key, module_value)
                structured_redis_storage(module_key, qubit.strip("q"), module_value)


def populate_node_parameters(
    node_name: str,
    is_node_calibrated: bool,
    qubits: list,
    couplers: list,
    redis_connection,
):
    # Populate the Redis database with node specific parameter values from the toml file
    transmon_configuration = toml.load(CONFIG.node)
    if node_name in transmon_configuration and not is_node_calibrated:
        node_specific_dict = transmon_configuration[node_name]["all"]
        for field_key, field_value in node_specific_dict.items():
            if isinstance(field_value, dict):
                for sub_field_key, sub_field_value in field_value.items():
                    sub_field_key = field_key + ":" + sub_field_key
                    for qubit in qubits:
                        redis_connection.hset(
                            f"transmons:{qubit}", sub_field_key, sub_field_value
                        )
                        structured_redis_storage(
                            sub_field_key, qubit.strip("q"), sub_field_value
                        )
                    for coupler in couplers:
                        redis_connection.hset(
                            f"couplers:{coupler}", sub_field_key, sub_field_value
                        )
                        structured_redis_storage(
                            sub_field_key, coupler, sub_field_value
                        )
            else:
                for qubit in qubits:
                    redis_connection.hset(f"transmons:{qubit}", field_key, field_value)
                    structured_redis_storage(field_key, qubit.strip("q"), field_value)
                for coupler in couplers:
                    redis_connection.hset(f"couplers:{coupler}", field_key, field_value)
                    structured_redis_storage(field_key, coupler, field_value)


def populate_quantities_of_interest(
    node_name: str,
    node_factory: NodeFactory,
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
        if qubit_qois is not None:
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
                        elif qoi == "r12:motzoi":
                            redis_connection.hset(f"transmons:{qubit}", qoi, "0")
                        structured_redis_storage(qoi, qubit.strip("q"), "nan")
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
                        structured_redis_storage(qoi, coupler, "nan")
                # flag for the calibration supervisor
                if not redis_connection.hexists(calibration_supervisor_key, node_name):
                    redis_connection.hset(f"cs:{coupler}", node_name, "not_calibrated")

    else:
        raise ValueError(
            f"Node {node_name} with base type {node} is not a valid Qubit or Coupler node. Cannot populate quantities of interest."
        )


def reset_all_nodes(nodes, qubits: list, couplers: list, redis_connection):
    for qubit in qubits:
        fields = redis_connection.hgetall(f"transmons:{qubit}").keys()
        key = f"transmons:{qubit}"
        cs_key = f"cs:{qubit}"
        for field in fields:
            redis_connection.hset(key, field, "nan")
            structured_redis_storage(key, qubit.strip("q"), None)
        for node in nodes:
            redis_connection.hset(cs_key, node, "not_calibrated")

    for coupler in couplers:
        fields = redis_connection.hgetall(f"couplers:{coupler}").keys()
        key = f"couplers:{coupler}"
        cs_key = f"cs:{coupler}"
        for field in fields:
            redis_connection.hset(key, field, "nan")
            structured_redis_storage(key, coupler, None)
        for node in nodes:
            redis_connection.hset(cs_key, node, "not_calibrated")


def fetch_redis_params(param: str, this_element: str):
    if "_" in this_element:
        name = "couplers"
    else:
        name = "transmons"
    redis_config = REDIS_CONNECTION.hgetall(f"{name}:{this_element}")
    return float(redis_config[param])
