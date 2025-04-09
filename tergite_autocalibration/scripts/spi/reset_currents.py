# This code is part of Tergite
#
# (C) Copyright Michele Faucci Giannelli 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from tergite_autocalibration.utils.dto.enums import MeasurementMode
from tergite_autocalibration.utils.hardware.spi import SpiDAC


if  __name__ == "main":
    couplers = ["q06_q07", "q08_q09", "q12_q13", "q14_q15"]
    spi = SpiDAC(couplers, measurement_mode=MeasurementMode.real)
    currents = {}
    for coupler in couplers:
        currents[coupler] = 0
    spi.ramp_current_serially(currents)
