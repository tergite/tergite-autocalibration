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
    # Start the wizard object
    # Now the thing is, how do we structure the wizard?
    # There are some general things to configure and:
    # - Device configuration
    # - Cluster configuration
    # - Hardware configuration

    from prompt_toolkit.shortcuts import checkboxlist_dialog

    results_array = checkboxlist_dialog(
        title="CheckboxList dialog",
        text="What would you like in your breakfast ?",
        values=[
            ("eggs", "Eggs"),
            ("bacon", "Bacon"),
            ("croissants", "20 Croissants"),
            ("daily", "The breakfast of the day"),
        ],
    ).run()

    typer.echo(results_array)

    results_array = checkboxlist_dialog(
        title="CheckboxList dialog",
        text="What would you like in your breakfast ?",
        values=[
            ("qubit", "Qubit"),
            ("bacon", "Bacon"),
            ("croissants", "20 Croissants"),
            ("daily", "The breakfast of the day"),
        ],
    ).run()

    # First thing, find the cluster
    # -> Enter the cluster name
    # -> IP can be detected automatically, but maybe it will not
    # -> Then you have to enter the IP manually

    # Do you want to identify the cluster? Y/N

    typer.echo(results_array)
