from qblox_instruments import SpiRack
from qblox_instruments.qcodes_drivers.spi_rack_modules import S4gModule
from qcodes import validators
import numpy as np
import time


dc_current_step = 5e-6
spi_mod_number = 1
spi_mod_name = f'module{spi_mod_number}'
spi = SpiRack('loki_rack', '/dev/ttyACM0')
spi.add_spi_module(spi_mod_number, S4gModule)
dac0 = spi.instrument_modules[spi_mod_name].instrument_modules['dac0']
dac1 = spi.instrument_modules[spi_mod_name].instrument_modules['dac1']
dac2 = spi.instrument_modules[spi_mod_name].instrument_modules['dac2']
dac3 = spi.instrument_modules[spi_mod_name].instrument_modules['dac3']
#---
print(f'{ dac0.current() = }')
print(f'{ dac1.current() = }')
print(f'{ dac2.current() = }')
print(f'{ dac3.current() = }')
#---
dac0.ramping_enabled(True)
dac1.ramping_enabled(True)
dac2.ramping_enabled(True)
dac3.ramping_enabled(True)
dac0.current(0)
dac1.current(0)
dac2.current(0)
dac3.current(0)
dac0.span('range_min_bi')
dac1.span('range_min_bi')
dac2.span('range_min_bi')
dac3.span('range_min_bi')
dac0.current(0)
dac1.current(0)
dac2.current(0)
dac3.current(0)
dac0.ramp_rate(10e-6)
dac1.ramp_rate(10e-6)
dac2.ramp_rate(10e-6)
dac3.ramp_rate(10e-6)
dac0.ramp_max_step(dc_current_step)
dac1.ramp_max_step(dc_current_step)

dac2.ramp_max_step(dc_current_step)
dac3.ramp_max_step(dc_current_step)
#---
print(f'{ dac0.current() = }')
print(f'{ dac1.current() = }')
print(f'{ dac2.current() = }')
print(f'{ dac3.current() = }')
#---
print(f'{ dac0.span() = }')
print(f'{ dac1.span() = }')
print(f'{ dac2.span() = }')
print(f'{ dac3.span() = }')
#---

dac0.current(0)
dac1.current(0)
dac2.current(0)
dac3.current(0)
while dac1.is_ramping():
            print(f'ramping {dac1.current()}')
            time.sleep(1)

print(f'{ dac1.current() = }')
# this_dac.ramp_max_step(dc_current_step)
# this_dac.current.vals = validators.Numbers(min_value=-3e-3, max_value=3e-3)
