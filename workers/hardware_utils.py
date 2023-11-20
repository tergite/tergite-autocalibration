from qblox_instruments import SpiRack
from qblox_instruments.qcodes_drivers.spi_rack_modules import S4gModule
from qcodes import validators
import numpy as np


def create_spi_dac(node):
    coupler = node.coupler
    coupler_spi_map = {
        'q16_q17': (1, 'dac0'), # slightly heating?
        'q17_q18': (1, 'dac1'),
        'q18_q19': (1, 'dac2'),
        'q19_q20': (1, 'dac3'), # slightly heating?
        'q16_q21': (2, 'dac2'),
        'q17_q22': (2, 'dac1'),
        'q18_q23': (2, 'dac0'),
        'q21_q22': (3, 'dac1'),
        'q22_q23': (3, 'dac2'), # badly heating?
        'q23_q24': (3, 'dac3'),
        'q20_q25': (3, 'dac0'),
        'q24_q25': (4, 'dac0'),
    }

    dc_current_step = np.diff(node.spi_samplespace['dc_currents'][coupler])[0]
    #ensure step is rounded in microAmpere:
    dc_current_step = round(dc_current_step / 1e-6) * 1e-6
    print(f'{ dc_current_step = }')
    spi_mod_number, dac_name = coupler_spi_map[coupler]
    spi_mod_name = f'module{spi_mod_number}'
    spi = SpiRack('loki_rack', '/dev/ttyACM0')
    spi.add_spi_module(spi_mod_number, S4gModule, reset_currents = False)
    this_dac = spi.instrument_modules[spi_mod_name].instrument_modules[dac_name]
    this_dac.ramping_enabled(False)
    this_dac.span('range_min_bi')
    # this_dac.current(0)
    this_dac.ramping_enabled(True)
    this_dac.ramp_rate(100e-6)
    this_dac.ramp_max_step(dc_current_step)
    this_dac.current.vals = validators.Numbers(min_value=-3e-3, max_value=3e-3)
    # for dac in spi.instrument_modules[spi_mod_name].submodules.values():
    # dac.current.vals = validators.Numbers(min_value=-2e-3, max_value=2e-3)
    return this_dac

