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

from pathlib import Path

import typer

from tergite_autocalibration.utils.logging.decorators import suppress_logging

backend_cli = typer.Typer()


@backend_cli.command(help="Save a redis backup.")
@suppress_logging
def save_file(file: Path):
    """
    Save a redis backup.

    Args:
        file: Output file path.
    """
    from tergite_autocalibration.config.globals import REDIS_CONNECTION
    from tergite_autocalibration.utils.backend.redis_backup import dump_redis_to_json

    # Do some file checks
    filepath = Path(file).resolve()
    if filepath.exists():
        confirm_ = typer.confirm(
            f"The output file '{filepath}' already exists. Do you want to overwrite it?"
        )
        if not confirm_:
            raise typer.Abort()

    dump_redis_to_json(REDIS_CONNECTION, file)


@backend_cli.command(help="Load a redis backup.")
@suppress_logging
def load_file(file: Path):
    """
    Load a redis backup.

    Args:
        file: Input file path.
    """
    from tergite_autocalibration.config.globals import REDIS_CONNECTION
    from tergite_autocalibration.utils.backend.redis_backup import load_json_to_redis

    # Do some file checks
    filepath = file.resolve()
    if not filepath.exists():
        typer.echo(f"Input file '{filepath}' does not exist.")
        raise typer.Abort()
    if not filepath.is_file():
        typer.echo(f"Input file '{filepath}' is not a file.")
        raise typer.Abort()

    load_json_to_redis(file, REDIS_CONNECTION)
