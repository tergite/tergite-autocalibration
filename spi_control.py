from qblox_instruments import SpiRack
from qblox_instruments.qcodes_drivers.spi_rack_modules import S4gModule

spi = SpiRack('lokiB', '/dev/ttyACM0')
spi.add_spi_module(1, S4gModule)
spi.add_spi_module(2, S4gModule)
spi.add_spi_module(3, S4gModule)

m1_dac0 = spi.instrument_modules['module1'].instrument_modules['dac0']
m1_dac1 = spi.instrument_modules['module1'].instrument_modules['dac1']
m1_dac2 = spi.instrument_modules['module1'].instrument_modules['dac2']
m1_dac3 = spi.instrument_modules['module1'].instrument_modules['dac3']
m2_dac0 = spi.instrument_modules['module2'].instrument_modules['dac0']
m2_dac1 = spi.instrument_modules['module2'].instrument_modules['dac1']
m2_dac2 = spi.instrument_modules['module2'].instrument_modules['dac2']
m2_dac3 = spi.instrument_modules['module2'].instrument_modules['dac3']
m3_dac0 = spi.instrument_modules['module3'].instrument_modules['dac0']
m3_dac1 = spi.instrument_modules['module3'].instrument_modules['dac1']
m3_dac2 = spi.instrument_modules['module3'].instrument_modules['dac2']
m3_dac3 = spi.instrument_modules['module3'].instrument_modules['dac3']

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
