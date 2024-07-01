import json
import time
from pathlib import Path
from typing import Dict

from qblox_instruments import Cluster, SpiRack
from qcodes import validators

from tergite_autocalibration.config.coupler_config import coupler_spi_map
from tergite_autocalibration.config.settings import REDIS_CONNECTION, HARDWARE_CONFIG
from tergite_autocalibration.utils.enums import MeasurementMode


def extract_cluster_port_mapping(qubit: str) -> Dict[str, str]:
    """
    TODO this is not a good implementation.
    Look into cashing.
    """
    with open(HARDWARE_CONFIG) as hw:
        hw_config = json.load(hw)

    clusters_in_hw = []
    for key in hw_config.keys():
        if "cluster" in key:
            clusters_in_hw.append(key)

    if len(clusters_in_hw) != 1:
        raise ValueError("Something Wrong with the Cluster HW_config")

    cluster_name = clusters_in_hw[0]
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


def find_serial_port():
    path = Path("/dev/")
    for file in path.iterdir():
        if file.name.startswith("ttyA"):
            port = str(file.absolute())
            break
    else:
        print("Couldn't find the serial port. Please check the connection.")
        port = None
    return port


class SpiDAC:
    def __init__(self, measurement_mode: MeasurementMode) -> None:
        port = find_serial_port()
        is_dummy = measurement_mode == MeasurementMode.dummy
        if port is not None:
            self.spi = SpiRack("loki_rack", port, is_dummy=is_dummy)

    def create_spi_dac(self, coupler: str):
        dc_current_step = 1e-6
        spi_mod_number, dac_name = coupler_spi_map[coupler]

        spi_mod_name = f"module{spi_mod_number}"
        if spi_mod_name not in self.spi.instrument_modules:
            self.spi.add_spi_module(spi_mod_number, "S4g")
        this_dac = self.spi.instrument_modules[spi_mod_name].instrument_modules[
            dac_name
        ]

        this_dac.span("range_min_bi")
        this_dac.current.vals = validators.Numbers(min_value=-3.1e-3, max_value=3.1e-3)

        this_dac.ramping_enabled(True)
        this_dac.ramp_rate(40e-6)
        this_dac.ramp_max_step(dc_current_step)
        return this_dac

    def set_dacs_zero(self) -> None:
        self.spi.set_dacs_zero()
        return

    def set_currenet_instant(self, dac, current) -> None:
        self.spi.set_current_instant(dac, current)

    def set_parking_current(self, coupler: str) -> None:
        dac = self.create_spi_dac(coupler)

        if REDIS_CONNECTION.hexists(f"transmons:{coupler}", "parking_current"):
            parking_current = float(
                REDIS_CONNECTION.hget(f"transmons:{coupler}", "parking_current")
            )
        else:
            raise ValueError("parking current is not present on redis")
        dac.current(parking_current)

        while dac.is_ramping():
            print(f"ramping {dac.current()}")
            time.sleep(1)
        print("Finished ramping")
        print(f"{ parking_current = }")
        print(f"{ dac.current() = }")
        return

    def set_dac_current(self, dac, target_current) -> None:
        dac.current(target_current)
        while dac.is_ramping():
            print(f"ramping {dac.current()}")
            time.sleep(1)
        print("Finished ramping")
        print(f"{ target_current = }")
        print(f"{ dac.current() = }")
        return
