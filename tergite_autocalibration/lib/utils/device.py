import json

from quantify_scheduler.device_under_test.quantum_device import QuantumDevice
from quantify_scheduler.json_utils import SchedulerJSONEncoder

from tergite_autocalibration.lib.utils.redis import (
    load_redis_config,
    load_redis_config_coupler,
)
from tergite_autocalibration.utils.extended_coupler_edge import (
    ExtendedCompositeSquareEdge,
)
from tergite_autocalibration.utils.extended_transmon_element import ExtendedTransmon


def configure_device(name, qubits: list[str], couplers: list[str]) -> QuantumDevice:
    device = QuantumDevice(f"Device_{name}")
    for channel, qubit in enumerate(qubits):
        transmon = ExtendedTransmon(qubit)
        transmon = load_redis_config(transmon, channel)
        device.add_element(transmon)

    if couplers is not None:
        for bus in couplers:
            control, target = bus.split(sep="_")
            coupler = ExtendedCompositeSquareEdge(control, target)
            coupler = load_redis_config_coupler(coupler)
            device.add_edge(coupler)

    return device


def save_serial_device(name: str, device: QuantumDevice, data_path) -> None:
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
