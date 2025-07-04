# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Chalmers Next Labs AB 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import json
import re
from typing import List, Union

import numpy as np
from quantify_scheduler.json_utils import SchedulerJSONDecoder, SchedulerJSONEncoder

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.config.legacy import dh
from tergite_autocalibration.tools.mss.convert import structured_redis_storage
from tergite_autocalibration.utils.dto import extended_transmon_element
from tergite_autocalibration.utils.dto.extended_coupler_edge import (
    ExtendedCompositeSquareEdge,
)
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon
from tergite_autocalibration.utils.dto.qoi import QOI
from tergite_autocalibration.utils.logging import logger

np.set_printoptions(legacy="1.25")


def load_redis_config(transmon: ExtendedTransmon, channel: int):
    qubit = transmon.name
    redis_config = REDIS_CONNECTION.hgetall(f"transmons:{qubit}")

    # get the transmon template in dictionary form
    serialized_transmon = json.dumps(transmon, cls=SchedulerJSONEncoder)
    decoded_transmon = json.loads(serialized_transmon)

    # the transmon modules are recognized by the ':' in the redis key
    transmon_redis_config = {k: v for k, v in redis_config.items() if ":" in k}
    device_redis_dict = {}
    for redis_entry_key, redis_value in transmon_redis_config.items():
        redis_value = float(redis_value)
        # e.g. 'clock_freqs:f01' is split to clock_freqs, f01
        submodule, field = redis_entry_key.split(":")
        device_redis_dict[submodule] = device_redis_dict.get(submodule, {}) | {
            field: redis_value
        }

    device_redis_dict["name"] = qubit

    for submodule in decoded_transmon["data"]:
        sub_module_content = decoded_transmon["data"][submodule]
        if isinstance(sub_module_content, dict) and submodule in device_redis_dict:
            redis_module_config = device_redis_dict[submodule]
            decoded_transmon["data"][submodule].update(redis_module_config)
        if "measure" in submodule:
            decoded_transmon["data"][submodule].update({"acq_channel": channel})

    encoded_transmon = json.dumps(decoded_transmon)

    # free the transmon
    transmon.close()

    # create a transmon with the same name but with updated config
    transmon = json.loads(
        encoded_transmon, cls=SchedulerJSONDecoder, modules=[extended_transmon_element]
    )

    return transmon


def load_redis_config_coupler(coupler: ExtendedCompositeSquareEdge):
    bus = coupler.name
    bus_qubits = bus.split("_")
    redis_config = REDIS_CONNECTION.hgetall(f"couplers:{bus}")
    try:
        coupler.clock_freqs.cz_freq(float(redis_config["cz_pulse_frequency"]))
        coupler.cz.square_amp(float(redis_config["cz_pulse_amplitude"]))
        coupler.cz.square_duration(float(redis_config["cz_pulse_duration"]))
        coupler.cz.cz_width(float(redis_config["cz_pulse_width"]))
        if dh.get_legacy("qubit_types")[bus_qubits[0]] == "Target":
            coupler.cz.parent_phase_correction(float(redis_config["cz_dynamic_target"]))
            coupler.cz.child_phase_correction(float(redis_config["cz_dynamic_control"]))
        else:
            coupler.cz.parent_phase_correction(
                float(redis_config["cz_dynamic_control"])
            )
            coupler.cz.child_phase_correction(float(redis_config["cz_dynamic_target"]))
    except:
        pass
    return coupler


def update_redis_trusted_values(
    node: str,
    this_element: str,
    qoi: QOI = None,
    redis_fields: Union[List[str], None] = None,
):
    """
    Update the redis trusted values for the qubit or coupler.
    Args:
        node: The node name
        this_element: The element name (qubit or coupler)
        qoi: The quantity of interest as QOI wrapped object
        redis_fields: List of redis fields for additional verification
    """

    if "_" in this_element:
        name = "couplers"
        _qoi_items = dict(qoi.analysis_result.items())
        if _are_two_qubit_in_qoi(_qoi_items):
            _save_parameters_in_qubits_in_coupler(
                node, this_element, name, _qoi_items, redis_fields
            )
        else:
            _save_parameters_in_coupler(node, this_element, name, qoi, redis_fields)

    else:
        name = "transmons"
        _save_parameters_in_transmon(node, this_element, name, qoi, redis_fields)


def _are_two_qubit_in_qoi(qoi: dict):
    return all(re.fullmatch(r"q\d{2}", key) for key in qoi)


def _save_parameters_in_transmon(
    node: str, this_element: str, name, qoi: QOI, redis_fields: List[str]
):
    """
    Saves the parameters for a single qubit in redis

    Args:
        node: Name of the node to update
        this_element: Name of the element to update, this will be e.g. q01
        name: Name of the property to update e.g. the qubit frequency
        qoi: The QOI object with the value to update
        redis_fields: redis fields from the node to be updated, this is for verification

    Raises:
        ValueError: if there are parameters in the qubit object that are not part of the node

    """
    analysis_successful = qoi.analysis_successful
    if analysis_successful:
        for qoi_name, qoi_result in qoi.analysis_result.items():
            if qoi_name not in redis_fields:
                raise ValueError(
                    f"The qoi {qoi_name} is not in redis fields: {redis_fields} for {this_element}"
                )
            value = qoi_result["value"]
            REDIS_CONNECTION.hset(f"{name}:{this_element}", qoi_name, value)
            # Setting the value in the standard redis storage
            structured_redis_storage(qoi_name, this_element.strip("q"), value)
            # Saving the error to the measured value
            error = qoi_result["error"]
            REDIS_CONNECTION.hset(f"{name}:{this_element}", qoi_name + "_error", error)
            # Setting the value in the standard redis storage
            structured_redis_storage(qoi_name + "_error", this_element.strip("q"), error)
        REDIS_CONNECTION.hset(f"cs:{this_element}", node, "calibrated")
    else:
        logger.warning(f"Analysis failed for {this_element}")


def _save_parameters_in_coupler(
    node: str, this_element: str, name: str, qoi: QOI, redis_fields: List[str]
):
    """
    Saves the parameters for a coupler in redis

    Args:
        node: Name of the node to update
        this_element: Name of the element to update, this will be e.g. q01_q02 for the coupler
        name: Name of the property to update e.g. the dc current
        qoi: The QOI object with the value to update
        redis_fields: redis fields from the node to be updated, this is for verification

    Raises:
        ValueError: if there are parameters in the qubit object that are not part of the node

    """

    analysis_successful = qoi.analysis_successful
    if analysis_successful:
        for qoi_name, qoi_result in qoi.analysis_result.items():
            if qoi_name not in redis_fields:
                raise ValueError(
                    f"The qoi {qoi_name} is not in redis fields: {redis_fields} for {this_element}"
                )
            value = qoi_result["value"]
            logger.info(f"Updating redis for {this_element} with {qoi_name}: {value}")
            REDIS_CONNECTION.hset(f"{name}:{this_element}", qoi_name, value)
            error = qoi_result["error"]
            logger.info(f"Updating redis for {this_element} with {qoi_name}_error: {error}")
            REDIS_CONNECTION.hset(f"{name}:{this_element}", qoi_name + "_error", error)
    REDIS_CONNECTION.hset(f"cs:{this_element}", node, "calibrated")


def _save_parameters_in_qubits_in_coupler(
    node: str, this_element: str, name: str, qoi: dict, redis_fields: List[str]
):
    """
    Saves the parameters for the qubits connected to a coupler, in redis

    Args:
        node: Name of the node to update
        this_element: Name of the element to update, this will be e.g. q01_q02, the qubits are extracted inside the function
        name: Name of the property to update e.g. the qubit frequency
        qoi: A dictionary that maps from qubit to the respective QOI
        redis_fields: redis fields from the node to be updated, this is for verification

    """

    qubits_in_coupler = [this_element[0:3], this_element[4:7]]
    for qubit in qubits_in_coupler:
        for transmon_parameter in redis_fields:
            REDIS_CONNECTION.hset(
                f"{name}:{this_element}:{qubit}",
                transmon_parameter,
                qoi[qubit][transmon_parameter],
            )
    REDIS_CONNECTION.hset(f"cs:{this_element}", node, "calibrated")
