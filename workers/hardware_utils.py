from qblox_instruments import SpiRack
from qcodes import validators
import time
import redis
from config_files.coupler_config import coupler_spi_map

redis_connection = redis.Redis(decode_responses=True)


class SpiDAC():
    def __init__(self) -> None:
        self.spi = SpiRack('loki_rack', '/dev/ttyACM0')

    def create_spi_dac(self, coupler: str):
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
        dc_current_step = 20e-6
        dc_current_step = round(dc_current_step / 1e-6) * 1e-6
        spi_mod_number, dac_name = coupler_spi_map[coupler]
        print(f'{ spi_mod_number = }')
        print(f'{ dac_name = }')
        spi_mod_name = f'module{spi_mod_number}'
        self.spi.add_spi_module(spi_mod_number, 'S4g')
        this_dac = self.spi.instrument_modules[spi_mod_name].instrument_modules[dac_name]
# IMPORTANT: First we set the span and then with set the currents to zero
        this_dac.span('range_min_bi')
        # self.spi.set_dacs_zero()
        this_dac.current.vals = validators.Numbers(min_value=-3.1e-3, max_value=3.1e-3)

        this_dac.ramping_enabled(True)
        this_dac.ramp_rate(20e-6)
        this_dac.ramp_max_step(dc_current_step)
# for dac in spi.instrument_modules[spi_mod_name].submodules.values():
# dac.current.vals = validators.Numbers(min_value=-2e-3, max_value=2e-3)
        return this_dac

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
    
    def set_dacs_zero(self) -> None:
        self.spi.set_dacs_zero()
        return