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

import typer

config_cli = typer.Typer()


@config_cli.command(help="Get a configuration value.")
def get():
    # Look up configuration value
    # Put it into the clipboard
    pass


@config_cli.command(help="Set a configuration value.")
def set():
    # Validate input
    # Write into configuration
    # Maybe can have a batch version of the command to set all values from a file
    pass


@config_cli.command(help="List available configuration values.")
def show():
    # Show all configuration values
    # What should the inputs be?
    pass


@config_cli.command(help="Run the configuration wizard.")
def wizard():
    from .controller import main

    main()
