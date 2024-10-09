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

from quantify_scheduler.json_utils import SchedulerJSONEncoder, SchedulerJSONDecoder

from tergite_autocalibration.config.data import dh
from tergite_autocalibration.config.settings import REDIS_CONNECTION
from tergite_autocalibration.utils import extended_transmon_element
from tergite_autocalibration.utils.extended_coupler_edge import CompositeSquareEdge
from tergite_autocalibration.utils.extended_transmon_element import ExtendedTransmon


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


def load_redis_config_coupler(coupler: CompositeSquareEdge):
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
        print(f"No coupler configuration found for {bus}")
        pass
    return
