# This code is part of Tergite
#
# (C) Copyright Tong Liu 2024
# (C) Copyright Chalmers Next Labs 2025
# (C) Copyright Michele Faucci Giannelli 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
import sys
import time
from pathlib import Path
from rich.progress import Progress
import time

import numpy as np
from colorama import Fore, Style
from qblox_instruments import SpiRack
from qcodes import validators

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.utils.logging import logger
from tergite_autocalibration.config.legacy import dh
from tergite_autocalibration.utils.dto.enums import MeasurementMode


def find_serial_port():
    path = Path("/dev/")
    for file in path.iterdir():
        if file.name.startswith("ttyA"):
            port = str(file.absolute())
            break
    else:
        logger.info("Couldn't find the serial port. Please check the connection.")
        port = None
    return port


class DummyDAC:
    def create_spi_dac(self, coupler: str):
        pass

    def set_dac_current(self, dac, target_current) -> None:
        logger.info(f"Dummy DAC to current {target_current}")


class SpiDAC:
    def __init__(self, couplers: list[str], measurement_mode: MeasurementMode):
        self.port = find_serial_port()
        self.is_dummy = (
            measurement_mode == MeasurementMode.dummy
            or measurement_mode == MeasurementMode.re_analyse
        )
        if self.port is not None:
            self.spi = SpiRack("loki_rack", self.port, is_dummy=self.is_dummy)
        else:
            raise ValueError("No serial port for the SPI")
        self.dacs_dictionary = {}
        for coupler in couplers:
            self.dacs_dictionary[coupler] = self.create_spi_dac(coupler)

    def create_spi_dac(self, coupler: str):
        spi_mod_number, dac_name = (
            dh.get_legacy("coupler_spi_mapping")[coupler]["spi_module_number"],
            dh.get_legacy("coupler_spi_mapping")[coupler]["dac_name"],
        )
        spi_mod_name = f"module{spi_mod_number}"

        if self.is_dummy:
            return f"Dummy_DAC_for_{spi_mod_name}_{dac_name}"

        dc_current_step = 1e-6

        if spi_mod_name not in self.spi.instrument_modules:
            self.spi.add_spi_module(spi_mod_number, "S4g")
        this_dac = self.spi.instrument_modules[spi_mod_name].instrument_modules[
            dac_name
        ]

        # WARNING: this command is bugged on the SPI firmware. When a DAC in operated
        # WARNING: for the first time, it sets the current to the minimum -0.25mA, which causes
        # WARNING: significant and dangerous heating. Follow the group instructions when you
        # WARNING: want to operate a DAC for the first time, or after a restart of the SPI rack.
        this_dac.span("range_min_bi")

        this_dac.current.vals = validators.Numbers(min_value=-3.1e-3, max_value=3.1e-3)

        this_dac.ramping_enabled(True)
        this_dac.ramp_rate(40e-6)
        this_dac.ramp_max_step(dc_current_step)
        return this_dac

    def set_dacs_zero(self) -> None:
        self.spi.set_dacs_zero()
        return

    def set_parking_current(self, coupler: str) -> None:

        if REDIS_CONNECTION.hexists(f"transmons:{coupler}", "parking_current"):
            parking_current = float(
                REDIS_CONNECTION.hget(f"transmons:{coupler}", "parking_current")
            )
        else:
            raise ValueError("parking current is not present on redis")

        self.ramp_current_serially({coupler: parking_current})
        return

    def set_dac_current(self, dac_values: dict[str, float]) -> None:
        if self.is_dummy:
            print(f"Dummy DAC to current {dac_values}. NO REAL CURRENT is generated")
            return
        self.ramp_current_serially(dac_values)

    def ramp_current_simultaneusly(self, dac_values: dict[str, float]):
        for coupler, target_current in dac_values.items():
            dac = self.dacs_dictionary[coupler]
            dac.current(target_current)
        ramp_counter = 0
        couplers = self.dacs_dictionary.keys()
        dacs = self.dacs_dictionary.values()
        logger.status(f"{Fore.YELLOW}{Style.DIM}{'Ramping current (mA)'}")
        logger.status(f"{couplers}", end=": ")
        while any([dac.is_ramping() for dac in dacs]):
            ramp_counter += 1
            print_termination = " -> "
            if ramp_counter % 8 == 0:
                print_termination = "\n"
            these_currents = np.array([dac.current() for dac in dacs])
            sys.stdout.write(f"{these_currents * 1000}", end=print_termination)
            sys.stdout.flush()
            time.sleep(1)
        logger.status(f"{Style.RESET_ALL} Ramping finished at {dac.current() * 1000:.4f} mA")
        print(end="\n")

    def ramp_current_serially(self, dac_values: dict[str, float]):
        for coupler, target_current in dac_values.items():
            dac = self.dacs_dictionary[coupler]
            dac.current(target_current)
            with Progress() as progress:
                task = progress.add_task("[yellow]Ramping current (mA) for coupler {coupler}", total=100)

                while dac.is_ramping():
                    current_mA = dac.current() * 1000
                    progress.update(task, advance=5, description=f"[cyan]{current_mA:.4f} mA")
                    time.sleep(1)  # Simulate delay



        logger.status(f"{Style.RESET_ALL} Ramping finished at {dac.current() * 1000:.4f} mA")
        print(end="\n")