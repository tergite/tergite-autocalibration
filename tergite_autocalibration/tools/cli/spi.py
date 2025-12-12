# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs AB 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import typer

from tergite_autocalibration.utils.logging.decorators import suppress_logging

spi_cli = typer.Typer()


@spi_cli.command(help="Print SPI currents.")
@suppress_logging
def status():
    import toml

    from tergite_autocalibration.config.globals import CONFIG
    from tergite_autocalibration.utils.dto.enums import MeasurementMode
    from tergite_autocalibration.utils.hardware.spi import SpiDAC

    spi_config = toml.load(CONFIG.spi)
    couplers = list(spi_config.keys())

    spi = SpiDAC(couplers, MeasurementMode.real)
    spi.print_currents()
