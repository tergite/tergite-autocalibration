# This code is part of Tergite
#
# (C) Copyright Tong Liu 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import time
from pathlib import Path

from colorama import Fore, Style
from qblox_instruments import SpiRack
from qcodes import validators

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.config.legacy import dh
from tergite_autocalibration.utils.dto.enums import MeasurementMode


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
        spi_mod_number, dac_name = (
            dh.get_legacy("coupler_spi_mapping")[coupler]["spi_module_number"],
            dh.get_legacy("coupler_spi_mapping")[coupler]["dac_name"],
        )

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
