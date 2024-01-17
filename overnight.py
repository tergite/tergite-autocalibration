import numpy as np
import itertools
import matplotlib
matplotlib.use('tkagg')

from workers.hardware_utils import SpiDAC
from qblox_instruments import SpiRack

def overnight20240108(s, DAC, dac):
    for current in np.arange(-0.95e-3, -1.5e-3, -0.05e-3):
        DAC.set_dac_current(dac, current)
        print(f'current: {current}')
        s.calibrate_node('qubit_01_spectroscopy_pulsed')
        for cz_pulse_amplitude in np.arange(0.1, 0.4, 0.03):
            s.calibrate_node("cz_chevron", cz_pulse_amplitude=cz_pulse_amplitude)

# def overnight20240111(s, DAC, dac):
#     paras = {
#         -1.0: (np.linspace(2.14e8, 2.20e8, 31), np.arange(0.37, 0.5, 0.03)),
#         -1.15: (np.linspace(2.18e8, 2.24e8, 31),  [0.33, 0.34, 0.35, 0.36, 0.37, 0.38, 0.39]),
#         -1.2: (np.linspace(2.14e8, 2.20e8, 31), np.arange(0.31, 0., 0.03)),
#         -1.3: (, [0.22, 0.28, 0.34])
#     }
            
def overnoon20240111(s, DAC, dac):
    """
    Test 640 MHz.
    """
    for current in np.arange(-0.95e-3, -1.5e-3, -0.05e-3):
        DAC.set_dac_current(dac, current)
        print(f'current: {current}')
        s.calibrate_node('qubit_01_spectroscopy_pulsed', spec_pulse_amplitudes=0.0005)
        for cz_pulse_amplitude in np.arange(0.1, 0.6, 0.03):
            s.calibrate_node("cz_chevron", cz_pulse_amplitude=cz_pulse_amplitude)

def overnoon20240117(s, DAC, dac):
    """
    Test 640 MHz.
    """
    for cz_pulse_amplitude in np.arange(0.5, 0.9, 0.05):
        s.calibrate_node("cz_chevron", cz_pulse_amplitude=cz_pulse_amplitude)