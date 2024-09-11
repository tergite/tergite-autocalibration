# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Amr Osman 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import time

from qblox_instruments import SpiRack
from qblox_instruments.qcodes_drivers.spi_rack_modules import S4gModule


def run_existing_spi_control_sequence():
    coupler_spi_map = {
        "q12_q13": (1, "dac1"),
    }

    coupler = "q12_q13"
    dc_current_step = 6e-6
    # ensure step is rounded in microAmpere:
    dc_current_step = round(dc_current_step / 1e-6) * 1e-6
    spi_mod_number, dac_name = coupler_spi_map[coupler]
    spi_mod_name = f"module{spi_mod_number}"
    spi = SpiRack("loki_rack", "/dev/ttyACM0")
    spi.add_spi_module(spi_mod_number, S4gModule)
    dac0 = spi.instrument_modules[spi_mod_name].instrument_modules["dac0"]
    dac1 = spi.instrument_modules[spi_mod_name].instrument_modules["dac1"]
    dac2 = spi.instrument_modules[spi_mod_name].instrument_modules["dac2"]
    dac3 = spi.instrument_modules[spi_mod_name].instrument_modules["dac3"]
    # ---
    print(f"{ dac0.current() = }")
    print(f"{ dac1.current() = }")
    print(f"{ dac2.current() = }")
    print(f"{ dac3.current() = }")
    # ---
    dac0.ramping_enabled(True)
    dac1.ramping_enabled(True)
    dac2.ramping_enabled(True)
    dac3.ramping_enabled(True)
    dac0.current(0)
    dac1.current(0)
    dac2.current(0)
    dac3.current(0)
    dac0.span("range_min_bi")
    dac1.span("range_min_bi")
    dac2.span("range_min_bi")
    dac3.span("range_min_bi")
    dac0.current(0)
    dac1.current(0)
    dac2.current(0)
    dac3.current(0)
    dac0.ramp_rate(20e-6)
    dac1.ramp_rate(20e-6)
    dac2.ramp_rate(20e-6)
    dac3.ramp_rate(20e-6)
    dac0.ramp_max_step(dc_current_step)
    dac1.ramp_max_step(dc_current_step)

    dac2.ramp_max_step(dc_current_step)
    dac3.ramp_max_step(dc_current_step)
    print(f"{ dac0.current() = }")
    print(f"{ dac1.current() = }")
    print(f"{ dac2.current() = }")
    print(f"{ dac3.current() = }")
    # ---
    print(f"{ dac0.span() = }")
    print(f"{ dac1.span() = }")
    print(f"{ dac2.span() = }")
    print(f"{ dac3.span() = }")
    # ---

    dac0.current(0)
    dac1.current(0)
    dac2.current(0)
    dac3.current(0)
    while dac1.is_ramping():
        print(f"ramping {dac1.current()}")
        time.sleep(1)

    print(f"{ dac1.current() = }")
    # this_dac.ramp_max_step(dc_current_step)
    # this_dac.current.vals = validators.Numbers(min_value=-3e-3, max_value=3e-3)


def run_new_spi_control_sequence():
    from qblox_instruments import SpiRack
    from qblox_instruments.qcodes_drivers.spi_rack_modules import S4gModule

    spi = SpiRack("lokiB", "/dev/ttyACM0")
    spi.add_spi_module(1, S4gModule)
    spi.add_spi_module(2, S4gModule)
    spi.add_spi_module(3, S4gModule)

    m1_dac0 = spi.instrument_modules["module1"].instrument_modules["dac0"]
    m1_dac1 = spi.instrument_modules["module1"].instrument_modules["dac1"]
    m1_dac2 = spi.instrument_modules["module1"].instrument_modules["dac2"]
    m1_dac3 = spi.instrument_modules["module1"].instrument_modules["dac3"]
    m2_dac0 = spi.instrument_modules["module2"].instrument_modules["dac0"]
    m2_dac1 = spi.instrument_modules["module2"].instrument_modules["dac1"]
    m2_dac2 = spi.instrument_modules["module2"].instrument_modules["dac2"]
    m2_dac3 = spi.instrument_modules["module2"].instrument_modules["dac3"]
    m3_dac0 = spi.instrument_modules["module3"].instrument_modules["dac0"]
    m3_dac1 = spi.instrument_modules["module3"].instrument_modules["dac1"]
    m3_dac2 = spi.instrument_modules["module3"].instrument_modules["dac2"]
    m3_dac3 = spi.instrument_modules["module3"].instrument_modules["dac3"]

    m1_dac0.ramping_enabled(True)
    m1_dac1.ramping_enabled(True)
    m1_dac2.ramping_enabled(True)
    m1_dac3.ramping_enabled(True)
    m2_dac0.ramping_enabled(True)
    m2_dac1.ramping_enabled(True)
    m2_dac2.ramping_enabled(True)
    m2_dac3.ramping_enabled(True)
    m3_dac0.ramping_enabled(True)
    m3_dac1.ramping_enabled(True)
    m3_dac2.ramping_enabled(True)
    m3_dac3.ramping_enabled(True)
    m1_dac0.current(0)
    m1_dac1.current(0)
    m1_dac2.current(0)
    m1_dac3.current(0)
    m2_dac0.current(0)
    m2_dac1.current(0)
    m2_dac2.current(0)
    m2_dac3.current(0)
    m3_dac0.current(0)
    m2_dac1.current(0)
    m2_dac2.current(0)
    m2_dac3.current(0)

    print(m1_dac0.current())
    print(m1_dac1.current())
    print(m1_dac2.current())
    print(m1_dac3.current())
    print(m2_dac0.current())
    print(m2_dac1.current())
    print(m2_dac2.current())
    print(m2_dac3.current())
    print(m3_dac0.current())
    print(m2_dac1.current())
    print(m2_dac2.current())
    print(m2_dac3.current())
