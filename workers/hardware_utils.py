from qblox_instruments import SpiRack
from qcodes import validators
import time
import redis

from config_files.settings import spiA_serial_port

redis_connection = redis.Redis(decode_responses=True)

def set_module_att(cluster):

    # Flux lines
    for module in cluster.modules[0:13]:
        module.out1_att(38)
    # print(module.name + '_att:'+ str(module.out1_att()) + 'dB')
    # Readout lines
    # for module in cluster.modules[15:17]:
    #     module.out0_att(6)
    # print(module.name + '_att:'+ str(module.out0_att()) + 'dB')

class SpiDAC():
    def __init__(self) -> None:
        self.spi = SpiRack('loki_rack', spiA_serial_port)

    def create_spi_dac(self, coupler: str):
        coupler_spi_map = {
            'q11_q12': (1, 'dac0'), # seems dead
            'q12_q13': (1, 'dac1'), # heating? about 1mK for a coupler spectroscopy
            'q13_q14': (1, 'dac2'),
            'q14_q15': (1, 'dac3'),
            # 'q16_q17': (1, 'dac0'), # slightly heating?
            # 'q17_q18': (1, 'dac1'),
            # 'q18_q19': (1, 'dac2'),
            # 'q19_q20': (1, 'dac3'), # slightly heating? , possibly +0.5mK for a coupler spectroscopy round
            # 'q16_q21': (2, 'dac2'),
            # 'q17_q22': (2, 'dac1'),
            # 'q18_q23': (2, 'dac0'),
            # 'q21_q22': (3, 'dac1'),
            # 'q22_q23': (3, 'dac2'), # badly heating?
            # 'q23_q24': (3, 'dac3'),
            # 'q20_q25': (3, 'dac0'),
            # 'q24_q25': (4, 'dac0'),
        }

        dc_current_step = 2e-6
        spi_mod_number, dac_name = coupler_spi_map[coupler]
        spi_mod_name = f'module{spi_mod_number}'
        if spi_mod_name not in self.spi.instrument_modules:
            self.spi.add_spi_module(spi_mod_number, 'S4g')
        this_dac = self.spi.instrument_modules[spi_mod_name].instrument_modules[dac_name]
        this_dac.ramping_enabled(True)
        this_dac.span('range_min_bi')
        this_dac.current.vals = validators.Numbers(min_value=-3.1e-3, max_value=3.1e-3)
        this_dac.ramp_rate(20e-6)
        this_dac.ramp_max_step(dc_current_step)
        return this_dac

    def set_parking_current(self, coupler: str, parking_current: float = None) -> None:

        dac = self.create_spi_dac(coupler)

        if parking_current is None:
            if redis_connection.hexists(f'couplers:{coupler}', 'parking_current'):
                parking_current = float(redis_connection.hget(f'couplers:{coupler}', 'parking_current'))
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
