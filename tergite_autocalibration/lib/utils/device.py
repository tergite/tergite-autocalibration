import json

from quantify_scheduler.device_under_test.quantum_device import QuantumDevice
from quantify_scheduler.json_utils import SchedulerJSONEncoder

from tergite_autocalibration.config.settings import HARDWARE_CONFIG
from tergite_autocalibration.lib.utils.redis import (
    load_redis_config,
    load_redis_config_coupler,
)
from tergite_autocalibration.utils.extended_coupler_edge import (
    ExtendedCompositeSquareEdge,
)
from tergite_autocalibration.utils.extended_transmon_element import ExtendedTransmon

with open(HARDWARE_CONFIG) as hw:
    hw_config = json.load(hw)

class DeviceConfiguration():
    def __init__(self, qubits: list[str], couplers: list[str]) -> None:
        self.qubits = qubits
        self.couplers = couplers
        self.transmons: dict[str, ExtendedTransmon] = {}
        self.edges: dict[str, ExtendedCompositeSquareEdge] = {}
        self.device: QuantumDevice
        
    def configure_device(self, name:str) -> QuantumDevice:
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

        device.hardware_config(hw_config)
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
