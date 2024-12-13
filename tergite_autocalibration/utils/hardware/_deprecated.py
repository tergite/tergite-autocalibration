# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Chalmers Next Labs 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
import json
from typing import Dict

from colorama import init as colorama_init
from qblox_instruments import Cluster

from tergite_autocalibration.config.env import CLUSTER_CONFIG

colorama_init()


def extract_cluster_port_mapping(qubit: str) -> Dict[str, str]:
    """
    TODO this is not a good implementation.
    Look into cashing.
    """
    with open(CLUSTER_CONFIG) as hw:
        hw_config = json.load(hw)

    # TODO: The cluster configuration here only seems to load the keys
    clusters_in_hw = []
    for key in hw_config.keys():
        if "cluster" in key:
            clusters_in_hw.append(key)

    if len(clusters_in_hw) != 1:
        raise ValueError("Something Wrong with the Cluster HW_config")

    cluster_name = clusters_in_hw[0]
    # TODO: The cluster configuration inside the hardware
    cluster_config = hw_config[cluster_name]

    # _cluster_port_mapping: {}
    for module, module_config in cluster_config.items():
        if "module" in module:
            try:
                complex_out_0 = module_config["complex_output_0"]
                portclock_config_0 = complex_out_0["portclock_configs"][0]
                qubit_port = portclock_config_0["port"]
                if qubit_port == qubit + ":mw":
                    return {"module": module, "complex_out": "complex_out_0"}
            except KeyError:
                portclock_config_0 = None
            try:
                complex_out_1 = module_config["complex_output_1"]
                portclock_config_1 = complex_out_1["portclock_configs"][0]
                qubit_port = portclock_config_1["port"]
                if qubit_port == qubit + ":mw":
                    return {"module": module, "complex_out": "complex_out_1"}
            except KeyError:
                portclock_config_1 = None
    else:
        raise ValueError("qubit not present in the configuration")


def set_qubit_attenuation(cluster: Cluster, qubit: str, att_in_db: int):
    qubit_to_out_map = extract_cluster_port_mapping(qubit)
    cluster_name, this_module_name = qubit_to_out_map["module"].split("_")
    this_output = qubit_to_out_map["complex_out"]
    this_module = cluster.instrument_modules[this_module_name]
    if this_output == "complex_out_0":
        this_module.out0_att(att_in_db)
    elif this_output == "complex_out_1":
        this_module.out1_att(att_in_db)
    else:
        raise ValueError(f"Uknown output: {this_output}")


def set_qubit_LO(cluster: Cluster, qubit: str, lo_frequency: float):
    qubit_to_out_map = extract_cluster_port_mapping(qubit)
    cluster_name, this_module_name = qubit_to_out_map["module"].split("_")
    this_output = qubit_to_out_map["complex_out"]
    this_module = cluster.instrument_modules[this_module_name]

    if this_output == "complex_out_0":
        this_module.out0_lo_freq(lo_frequency)
        this_module.out0_lo_en(True)
    elif this_output == "complex_out_1":
        this_module.out1_lo_freq(lo_frequency)
        this_module.out1_lo_en(True)
    else:
        raise ValueError(f"Unknown output: {this_output}")
