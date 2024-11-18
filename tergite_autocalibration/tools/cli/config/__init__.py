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
import shutil
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


@config_cli.command(help="Save the whole configuration snapshot.")
def save(
    filepath: Annotated[
        str,
        typer.Option(
            "--filepath",
            "-f",
            help="Path to store the configuration at.",
        ),
    ] = None,
    as_zip: Annotated[
        bool,
        typer.Option(
            "--as-zip",
            "-z",
            is_flag=True,
            help="If --no-zip, the configuration files will be stored into a folder and not zipped.",
        ),
    ] = False,
):
    """
    CLI endpoint to save configuration packages.
    Will store the configuration that is currently located in the root directory of the autocalibration.

    Args:
        filepath: Path to where the configuration will be saved
        as_zip: Whether to zip the configuration package

    Returns:

    """

    from tergite_autocalibration.config.settings import ROOT_DIR
    from tergite_autocalibration.config.handler import MetaConfiguration

    # Check whether filepath parameter is given
    if filepath is None:
        typer.echo("Please provide a path with the -f parameter.")
        return

    # Create the absolute path from the filepath
    abs_filepath = os.path.abspath(filepath)

    # This is the path to the meta configuration for the current application
    meta_config_path = os.path.join(ROOT_DIR, "configuration.meta.toml")

    # Abort if there is no such meta configuration
    if not os.path.exists(meta_config_path):
        typer.echo(
            "Cannot find meta configuration.\n"
            "Please make sure your autocalibration is properly configured before trying to save a configuration package"
        )
        return

    # Otherwise load the meta configuration object
    meta_config = MetaConfiguration.from_toml(meta_config_path)

    # Basic check whether there might be conflicting files at the target location that might be overwritten
    if os.path.exists(abs_filepath):
        typer.confirm(
            "The filepath where you want to store your configuration package already exists.\n"
            "Do you wish to continue?",
            abort=True,
        )
    # Copy the configuration package to the target location
    configuration_to_export = meta_config.copy(abs_filepath)

    # If the configuration should be saved as zip file, then zip it and remove the folder
    if as_zip:
        shutil.make_archive(abs_filepath, format="zip", root_dir=abs_filepath)
        configuration_to_export.delete()


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
    """
    CLI endpoint to load configuration packages. Will copy the package to the root directory.

    Args:
        filepath: Path to a configuration package
        template: Name to a configuration package from the templates folder

    Returns:

    """

    from tergite_autocalibration.config.handler import MetaConfiguration
    from tergite_autocalibration.config.settings import ROOT_DIR

    # This is the case where a template path is given to the know templates directory
    if template is not None:
        meta_config = MetaConfiguration.from_toml(
            os.path.join(config_templates_path, template, "configuration.meta.toml")
        )

    # This is the case where a filepath in the filesystem is given
    elif filepath is not None:
        # Make sure that it is the absolute filepath to the source
        filepath = os.path.abspath(filepath)
        # Check, because it could be either the path to the meta configuration or its parent directory
        if filepath.endswith("configuration.meta.toml"):
            filepath = os.path.join(filepath, "configuration.meta.toml")
        meta_config = MetaConfiguration.from_toml(filepath)

    # In any other case load the .default template for the meta configuration
    else:
        typer.echo(
            "No configuration package specified. Loading default configuration..."
        )
        meta_config = MetaConfiguration.from_toml(
            os.path.join(config_templates_path, ".default", "configuration.meta.toml")
        )

    # Basic check whether there is not already a configuration package in place that would be overwritten
    if os.path.exists(os.path.join(ROOT_DIR, "configuration.meta.toml")):
        typer.confirm(
            "There is already a configuration package loaded, do you want to overwrite it?",
            abort=True,
        )

    # Copy the meta configuration to the root directory
    meta_config.copy(ROOT_DIR)


@config_cli.command(help="List available configuration values.")
def show():
    # Show all configuration values
    # What should the inputs be?
    raise NotImplementedError()


@config_cli.command(help="Run the configuration wizard.")
def wizard():
    from .controller import main

    main()
