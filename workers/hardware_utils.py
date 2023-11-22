from qblox_instruments import SpiRack
from qblox_instruments.qcodes_drivers.spi_rack_modules import S4gModule
from qcodes import validators
import numpy as np
import time


def create_spi_dac(coupler: str):
    coupler_spi_map = {
        'q16_q17': (1, 'dac0'), # slightly heating?
        'q17_q18': (1, 'dac1'),
        'q18_q19': (1, 'dac2'),
        'q19_q20': (1, 'dac3'), # slightly heating? , possibly +0.5mK for a coupler spectroscopy round
        'q16_q21': (2, 'dac2'),
        'q17_q22': (2, 'dac1'),
        'q18_q23': (2, 'dac0'),
        'q21_q22': (3, 'dac1'),
        'q22_q23': (3, 'dac2'), # badly heating?
        'q23_q24': (3, 'dac3'),
        'q20_q25': (3, 'dac0'),
        'q24_q25': (4, 'dac0'),
    }

    # dc_current_step = np.diff(node.spi_samplespace['dc_currents'][coupler])[0]
    # ensure step is rounded in microAmpere:
    dc_current_step = 100e-6
    dc_current_step = round(dc_current_step / 1e-6) * 1e-6
    spi_mod_number, dac_name = coupler_spi_map[coupler]
    print(f'{ spi_mod_number = }')
    print(f'{ dac_name = }')
    spi_mod_name = f'module{spi_mod_number}'
    spi = SpiRack('loki_rack', '/dev/ttyACM0')
    spi.add_spi_module(spi_mod_number, 'S4g')
    this_dac = spi.instrument_modules[spi_mod_name].instrument_modules[dac_name]
    # IMPORTANT: First we set the span and then with set the currents to zero
    this_dac.span('range_min_bi')
    spi.set_dacs_zero()
    this_dac.current.vals = validators.Numbers(min_value=-3.1e-3, max_value=3.1e-3)

    this_dac.ramping_enabled(True)
    this_dac.ramp_rate(500e-6)
    this_dac.ramp_max_step(dc_current_step)
    # for dac in spi.instrument_modules[spi_mod_name].submodules.values():
    # dac.current.vals = validators.Numbers(min_value=-2e-3, max_value=2e-3)
    return this_dac
