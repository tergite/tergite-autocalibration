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

# fmt: off
    couplers = ["q06_q07", "q07_q08", "q08_q09", "q09_q10",
                "q11_q12", "q12_q13", "q13_q14", "q14_q15",
                "q06_q11", "q07_q12", "q08_q13", "q09_q14", "q10_q15",
                "q11_q16", "q12_q17", "q13_q18", "q14_q19", "q15_q20",
                ]
# fmt: on

    spi = SpiDAC(couplers, measurement_mode=MeasurementMode.real)
    spi.print_currents()
