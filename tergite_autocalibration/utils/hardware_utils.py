# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import json
import time
from pathlib import Path
from typing import Dict

from qblox_instruments import Cluster, SpiRack
from qcodes import validators

from tergite_autocalibration.config.coupler_config import coupler_spi_map
from tergite_autocalibration.config.settings import REDIS_CONNECTION, HARDWARE_CONFIG
from tergite_autocalibration.utils.dto.enums import MeasurementMode

from colorama import Fore
from colorama import Style
from colorama import init as colorama_init

colorama_init()


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


class DummyDAC:
    def create_spi_dac(self, coupler: str):
        pass

    def set_dac_current(self, dac, target_current) -> None:
        print(f"Dummy DAC to current {target_current}")


class SpiDAC:
    def __init__(self, measurement_mode: MeasurementMode) -> None:
        port = find_serial_port()
        self.is_dummy = measurement_mode == MeasurementMode.dummy
        if port is not None:
            self.spi = SpiRack("loki_rack", port, is_dummy=self.is_dummy)

    def create_spi_dac(self, coupler: str):
        if self.is_dummy:
            return
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

        # dac.current(parking_current)
        self.ramp_current(dac, parking_current)
        print("Finished ramping")
        print(f"Current is now: { dac.current() * 1000:.4f} mA")
        return

    def set_dac_current(self, dac, target_current) -> None:
        if self.is_dummy:
            print(
                f"Dummy DAC to current {target_current}. NO REAL CURRENT is generated"
            )
            return
        self.ramp_current(dac, target_current)

    def ramp_current(self, dac, target_current):
        dac.current(target_current)
        ramp_counter = 0
        print(f"{Fore.YELLOW}{Style.DIM}{'Ramping current (mA)'}")
        while dac.is_ramping():
            ramp_counter += 1
            print_termination = " -> "
            if ramp_counter % 8 == 0:
                print_termination = "\n"
            print(f"{dac.current() * 1000:3.4f}", end=print_termination, flush=True)
            time.sleep(1)
        print(f"{Style.RESET_ALL}")
        print(end="\n")
