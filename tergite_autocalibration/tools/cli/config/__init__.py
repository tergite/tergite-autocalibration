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
            "-p",
            help="Path to store the configuration at. "
            "If it ends with .zip, the configuration package will become an archive",
        ),
    ] = None,
    as_zip: Annotated[
        bool,
        typer.Option(
            "--as-zip",
            "-z",
            is_flag=True,
            help="If --as-zip, the configuration files will be archived.",
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

    from tergite_autocalibration.config.globals import ENV
    from tergite_autocalibration.config.package import ConfigurationPackage

    # Check whether filepath parameter is given
    if filepath is None:
        typer.echo("Please provide a path with the -f parameter.")
        return

    # Automatically set the .zip parameter if the output is a zip file
    if filepath.endswith(".zip"):
        filepath = filepath.removesuffix(".zip")
        as_zip = True

    # Create the absolute path from the filepath
    abs_filepath = os.path.abspath(filepath)

    # This is the path to the meta configuration for the current application
    if abs_filepath.endswith("configuration.meta.toml"):
        abs_filepath = os.path.dirname(abs_filepath)
    meta_config_path = os.path.join(ENV.root_dir, "configuration.meta.toml")

    # Abort if there is no such meta configuration
    if not os.path.exists(meta_config_path):
        typer.echo(
            "Cannot find meta configuration.\n"
            "Please make sure your autocalibration is properly configured before trying to save a configuration package"
        )
        return

    # Otherwise load the meta configuration object
    configuration_package = ConfigurationPackage.from_toml(meta_config_path)

    # Basic check whether there might be conflicting files at the target location that might be overwritten
    if os.path.exists(abs_filepath):
        typer.confirm(
            "The filepath where you want to store your configuration package already exists.\n"
            "Do you wish to continue?",
            abort=True,
        )
    # Copy the configuration package to the target location
    configuration_package.copy(abs_filepath)

    # If the configuration should be saved as zip file, then zip it and remove the folder
    if as_zip:
        shutil.make_archive(abs_filepath, format="zip", root_dir=abs_filepath)
        # Remove the temporary directory from the zipping process
        shutil.rmtree(abs_filepath)


@config_cli.command(help="Restore and load a configuration snapshot.")
def load(
    filepath: Annotated[
        str,
        typer.Option(
            "--filepath",
            "-f",
            "-p",
            help="Path to load the configuration from.",
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

    from tergite_autocalibration.config.package import ConfigurationPackage
    from tergite_autocalibration.config.globals import ENV

    # Basic check whether there is not already a configuration package in place that would be overwritten
    if os.path.exists(os.path.join(ENV.root_dir, "configuration.meta.toml")):
        typer.confirm(
            "There is already a configuration package loaded, do you want to overwrite it?",
            abort=True,
        )

    # We have to store the path of the temporary files from unzipping to clean-up later
    clean_temp_folder = None

    # This is the case where a template path is given to the know templates directory
    if template is not None:
        configuration_package = ConfigurationPackage.from_toml(
            os.path.join(config_templates_path, template, "configuration.meta.toml")
        )

    # This is the case where a filepath in the filesystem is given
    elif filepath is not None:
        # Make sure that it is the absolute filepath to the source
        filepath = os.path.abspath(filepath)
        # Check whether it is an archive, because then it would load it from the .zip
        if filepath.endswith(".zip"):
            clean_temp_folder = filepath.removesuffix(".zip")
            if os.path.exists(clean_temp_folder):
                typer.confirm(
                    f"The directory {clean_temp_folder} already exists and would be overwritten during loading.\n"
                    "Do you want to proceed?",
                    abort=True,
                )
            configuration_package = ConfigurationPackage.from_zip(filepath)
        else:
            # Check, because it could be either the path to the meta configuration or its parent directory
            if not filepath.endswith("configuration.meta.toml"):
                filepath = os.path.join(filepath, "configuration.meta.toml")
            configuration_package = ConfigurationPackage.from_toml(filepath)

    # In any other case load the .default template for the meta configuration
    else:
        typer.echo(
            "No configuration package specified. Loading default configuration..."
        )
        configuration_package = ConfigurationPackage.from_toml(
            os.path.join(config_templates_path, ".default", "configuration.meta.toml")
        )

    # Copy the meta configuration to the root directory
    configuration_package.copy(ENV.root_dir)

    # Check whether there is anything to clean
    if clean_temp_folder is not None:
        shutil.rmtree(clean_temp_folder)


@config_cli.command(help="List available configuration values.")
def show():
    # Show all configuration values
    # What should the inputs be?
    raise NotImplementedError()


@config_cli.command(help="Run the configuration wizard.")
def wizard():
    from .controller import main

    main()
