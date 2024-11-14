# This code is part of Tergite
#
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

config_cli = typer.Typer()


@config_cli.command(help="Get a configuration value.")
def get():
    # Look up configuration value
    # Put it into the clipboard
    raise NotImplementedError()


@config_cli.command(help="Set a configuration value.")
def set():
    # Validate input
    # Write into configuration
    # Maybe can have a batch version of the command to set all values from a file
    raise NotImplementedError()


@config_cli.command(help="Save the whole configuration snapshot.")
def save(
    filepath: Annotated[
        str,
        typer.Option(
            "--filepath",
            "-f",
            help="Path to store the configuration at. If not set, it will assume the current directory.",
        ),
    ] = None,
    no_zip: Annotated[
        bool,
        typer.Option(
            "--no-zip",
            is_flag=True,
            help="If --no-zip, the configuration files will be stored into a folder and not zipped.",
        ),
    ] = False,
    no_env: Annotated[
        bool,
        typer.Option(
            "--no-env",
            is_flag=True,
            help="If --no-env, the configuration package will not contain the .env file.",
        ),
    ] = False,
):
    import os.path

    from tergite_autocalibration.config.helpers import save_configuration_snapshot
    from .helpers import get_cwd

    if filepath is None:
        filepath = os.path.join(get_cwd(), "configuration_snapshot")

    save_configuration_snapshot(filepath, zip_file=not no_zip, save_env=not no_env)


@config_cli.command(help="Restore and load a configuration snapshot.")
def load():
    raise NotImplementedError()


@config_cli.command(help="List available configuration values.")
def show():
    # Show all configuration values
    # What should the inputs be?
    pass


@config_cli.command(help="Run the configuration wizard.")
def wizard():
    from .controller import main

    main()
