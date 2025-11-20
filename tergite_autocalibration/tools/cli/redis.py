# This code is part of Tergite
#
# (C) Copyright Stefan Hill 2024
# (C) Copyright Michele Faucci Giannelli 2024
# (C) Copyright Chalmers Next Labs 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from typing import Annotated

import typer

from tergite_autocalibration.utils.logging.decorators import suppress_logging

redis_cli = typer.Typer()


@redis_cli.command(help="Save a redis backup.")
@suppress_logging
def save_backup(
    output: Annotated[
        str,
        typer.Option(
            "--output",
            "-o",
            help="Output file path.",
        ),
    ] = None,
    port: Annotated[
        str,
        typer.Option(
            "--port",
            "-p",
            help="Port for the redis database. Default: Loads the port from .env configuration.",
        ),
    ] = None,
    host: Annotated[
        bool,
        typer.Option(
            "--host",
            "-h",
            help="Host of the redis database. Default: Loads the host from .env configuration.",
        ),
    ] = False,
):
    pass
