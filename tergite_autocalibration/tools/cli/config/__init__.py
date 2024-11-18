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

import os
from pathlib import Path
from typing import Annotated

import typer

config_cli = typer.Typer()

config_templates_path = os.path.join(
    Path(__file__).parent.parent.parent.parent.parent, "templates"
)
template_names = [
    entry_.name for entry_ in os.scandir(config_templates_path) if entry_.is_dir()
]


def complete_template_name(incomplete: str):
    for template_name in template_names:
        if template_name.startswith(incomplete):
            yield template_name


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
    # no_zip: Annotated[
    #     bool,
    #     typer.Option(
    #         "--no-zip",
    #         is_flag=True,
    #         help="If --no-zip, the configuration files will be stored into a folder and not zipped.",
    #     ),
    # ] = False,
    # no_env: Annotated[
    #     bool,
    #     typer.Option(
    #         "--no-env",
    #         is_flag=True,
    #         help="If --no-env, the configuration package will not contain the .env file.",
    #     ),
    # ] = False,
):
    from tergite_autocalibration.config.settings import ROOT_DIR
    from tergite_autocalibration.config.handler import MetaConfiguration

    if filepath is None:
        typer.echo(
            "Cannot store configuration package, please provide a valid filepath."
        )
        return

    abs_filepath = os.path.abspath(filepath)
    typer.echo(abs_filepath)

    meta_config_path = os.path.join(ROOT_DIR, "configuration.meta.toml")

    if not os.path.exists(meta_config_path):
        typer.echo(
            "Cannot find meta configuration. "
            "Please make sure your autocalibration is properly configured before trying to save a configuration package"
        )
        return

    meta_config = MetaConfiguration.from_toml(meta_config_path)

    if os.path.exists(abs_filepath):
        overwrite = typer.confirm(
            "The filepath where you want to store your configuration package already exists. "
            "Do you wish to continue?",
            abort=True,
        )
        if overwrite:
            meta_config.copy(abs_filepath)
        else:
            typer.echo("Aborting...")
    else:
        meta_config.copy(abs_filepath)


@config_cli.command(help="Restore and load a configuration snapshot.")
def load(
    filepath: Annotated[
        str,
        typer.Option(
            "--filepath",
            "-f",
            help="Path to store the configuration at. If not set, it will assume the current directory.",
        ),
    ] = None,
    template: Annotated[
        str,
        typer.Option(
            "--template",
            "-t",
            help="Shortcut to load the configuration from a template in the templates path.",
            autocompletion=complete_template_name,
        ),
    ] = None,
):
    from tergite_autocalibration.config.handler import MetaConfiguration
    from tergite_autocalibration.config.settings import ROOT_DIR

    if template is not None:
        meta_config = MetaConfiguration.from_toml(
            os.path.join(config_templates_path, template, "configuration.meta.toml")
        )
    elif filepath is not None:
        meta_config = MetaConfiguration.from_toml(
            os.path.join(filepath, "configuration.meta.toml")
        )
    else:
        typer.echo(
            "No configuration package specified. Loading default configuration..."
        )
        meta_config = MetaConfiguration.from_toml(
            os.path.join(config_templates_path, ".default", "configuration.meta.toml")
        )
    meta_config.copy(ROOT_DIR)


@config_cli.command(help="List available configuration values.")
def show():
    # Show all configuration values
    # What should the inputs be?
    pass


@config_cli.command(help="Run the configuration wizard.")
def wizard():
    from .controller import main

    main()
