# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import json

from quantify_scheduler.device_under_test.quantum_device import QuantumDevice
from quantify_scheduler.json_utils import SchedulerJSONEncoder

from tergite_autocalibration.config.globals import CONFIG
from tergite_autocalibration.lib.utils.redis import (
    load_redis_config,
    load_redis_config_coupler,
)
from tergite_autocalibration.utils.dto.extended_coupler_edge import (
    ExtendedCompositeSquareEdge,
)
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon


class DeviceConfiguration:
    def __init__(self, qubits: list[str], couplers: list[str]) -> None:
        self.qubits = qubits
        self.couplers = couplers
        self.transmons: dict[str, ExtendedTransmon] = {}
        self.edges: dict[str, ExtendedCompositeSquareEdge] = {}
        self.device: QuantumDevice

    def configure_device(self, name: str) -> QuantumDevice:
        device = QuantumDevice(f"Device_{name}")
        for channel, qubit in enumerate(self.qubits):
            transmon = ExtendedTransmon(qubit)
            transmon = load_redis_config(transmon, channel)
            device.add_element(transmon)
            self.transmons[qubit] = transmon

        if self.couplers is not None:
            for coupler in self.couplers:
                control, target = coupler.split(sep="_")
                edge = ExtendedCompositeSquareEdge(control, target)
                edge = load_redis_config_coupler(edge)
                device.add_edge(edge)
                self.edges[coupler] = edge

        device.hardware_config(CONFIG.cluster)
        self.device = device
        return device

    def close_device(self):
        # after the compilation_config is acquired, free the transmon resources
        for transmon in self.transmons.values():
            transmon.close()
        if self.couplers is not None:
            for edge in self.edges.values():
                edge.close()

        self.device.close()

    def save_serial_device(self, name: str, device: QuantumDevice, data_path) -> None:
        # create a transmon with the same name but with updated config
        # get the transmon template in dictionary form
        serialized_device = json.dumps(device, cls=SchedulerJSONEncoder)
        decoded_device = json.loads(serialized_device)
        serial_device = {}
        for element, element_config in decoded_device["data"]["elements"].items():
            serial_config = json.loads(element_config)
            serial_device[element] = serial_config

        data_path.mkdir(parents=True, exist_ok=True)
        with open(f"{data_path}/{name}.json", "w") as f:
            json.dump(serial_device, f, indent=4)
