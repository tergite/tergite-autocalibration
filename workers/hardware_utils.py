from qblox_instruments import SpiRack
from qcodes import validators
import time
import redis
from pathlib import Path
from config_files.coupler_config import coupler_spi_map

from config_files.settings import spiA_serial_port

redis_connection = redis.Redis(decode_responses=True)

def find_serial_port():
    path = Path('/dev/')
    for file in path.iterdir():
        if file.name.startswith('ttyA'):
            port = str(file.absolute())
            break
    else:
        print("Couldn't find the serial port. Please check the connection.")
        port = None
    return port

class SpiDAC():
    def __init__(self) -> None:
        port = find_serial_port()
        if port is not None:
            self.spi = SpiRack('loki_rack', port)

    def create_spi_dac(self, coupler: str):

        dc_current_step = 1e-6
        spi_mod_number, dac_name = coupler_spi_map[coupler]
        spi_mod_name = f'module{spi_mod_number}'
        if spi_mod_name not in self.spi.instrument_modules:
            self.spi.add_spi_module(spi_mod_number, 'S4g')
        this_dac = self.spi.instrument_modules[spi_mod_name].instrument_modules[dac_name]

        this_dac.span('range_min_bi')
        this_dac.current.vals = validators.Numbers(min_value=-3.1e-3, max_value=3.1e-3)

        this_dac.ramping_enabled(True)
        this_dac.ramp_rate(20e-6)
        this_dac.ramp_max_step(dc_current_step)
        return this_dac

    def set_dacs_zero(self) -> None:
        self.spi.set_dacs_zero()
        return

    def set_currenet_instant(self, dac , current) -> None:
        self.spi.set_current_instant(dac, current)

    def set_parking_current(self, coupler: str) -> None:

        dac = self.create_spi_dac(coupler)

        if redis_connection.hexists(f'transmons:{coupler}', 'parking_current'):
            parking_current = float(redis_connection.hget(f'transmons:{coupler}', 'parking_current'))
        else:
            raise ValueError('parking current is not present on redis')
        dac.current(parking_current)

        while dac.is_ramping():
            print(f'ramping {dac.current()}')
            time.sleep(1)
        print('Finished ramping')
        print(f'{ parking_current = }')
        print(f'{ dac.current() = }')
        return

    def set_dac_current(self, dac, parking_current) -> None:
        dac.current(parking_current)
        while dac.is_ramping():
            print(f'ramping {dac.current()}')
            time.sleep(1)
        print('Finished ramping')
        print(f'{ parking_current = }')
        print(f'{ dac.current() = }')
        return
