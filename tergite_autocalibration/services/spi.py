# This code is part of Tergite
#
# (C) Copyright Michele Faucci Giannelli 2025
# (C) Copyright Chalmers Next Labs AB 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import toml

from tergite_autocalibration.config.globals import CONFIG
from tergite_autocalibration.utils.dto.enums import MeasurementMode
from tergite_autocalibration.utils.hardware.spi import SpiDAC

_spi_config = toml.load(CONFIG.spi)
_couplers = list(_spi_config.keys())
_spi = SpiDAC(_couplers, MeasurementMode.real, name="spi_service")


def print_spi_currents():
    """
    Print the current for all DACs defined in the SPI configuration
    """
    _spi.print_currents()


def reset_spi_currents():
    """
    Reset the currents for all DACs defined in the SPI configuration to 0
    """
    currents = {coupler: 0 for coupler in _couplers}
    _spi.ramp_current_serially(currents)
    _spi.print_currents()
