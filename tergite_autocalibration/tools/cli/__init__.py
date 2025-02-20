# This code is part of Tergite
#
# (C) Copyright Stefan Hill 2024
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from typing import Annotated, Union

import typer

from tergite_autocalibration.tools.cli.calibration import calibration_cli
from tergite_autocalibration.tools.cli.cluster import cluster_cli
from tergite_autocalibration.tools.cli.config import config_cli
from tergite_autocalibration.tools.cli.graph import graph_cli
from tergite_autocalibration.tools.cli.node import node_cli

cli_kwargs = {"no_args_is_help": True}

cli = typer.Typer(**cli_kwargs, pretty_exceptions_enable=False)

cli.add_typer(
    calibration_cli,
    **cli_kwargs,
    name="calibration",
    help="Start the calibration supervisor.",
)
cli.add_typer(
    node_cli,
    **cli_kwargs,
    name="node",
    help="Handle operations related to the node.",
)
cli.add_typer(
    cluster_cli,
    **cli_kwargs,
    name="cluster",
    help="Handle operations related to the cluster.",
)
cli.add_typer(
    graph_cli,
    **cli_kwargs,
    name="graph",
    help="Handle operations related to the calibration graph.",
)
cli.add_typer(
    config_cli,
    **cli_kwargs,
    name="config",
    help="Functions related to the configuration.",
)


@cli.command(help="Quickly runs to set reasonable defaults for the configuration.")
def quickstart(
    qubits: Annotated[
        str,
        typer.Option(
            "--qubits",
            "-q",
            help='Qubit input e.g. "q00,q01,q02,q03,q04" or "q01-q05" or "q01-q06, q08".'
            'If the input is an integer e.g. 3, it will generate "q01,q02,q03".',
        ),
    ] = None
):
    """
    This is loading the template to the root dir and fills it with the input qubits.

    Args:
        qubits: Qubit input e.g. "q00,q01,q02,q03,q04" or "q01-q05" or "q01-q06, q08"
    """
    import os

    from jinja2 import Template

    from tergite_autocalibration.config.globals import ENV
    from tergite_autocalibration.config.package import ConfigurationPackage
    from tergite_autocalibration.tools.cli.config import load
    from tergite_autocalibration.utils.io.parsers import parse_input_qubits
    from tergite_autocalibration.utils.misc.helpers import generate_n_qubit_list

    # This is the case where the qubit input indicates the total number of qubits
    try:
        qubits = int(qubits)
        qubits_ = generate_n_qubit_list(qubits)

    # This is the case where the qubits are specified in a string and then parsed
    except ValueError:
        if isinstance(qubits, str):
            qubits_ = parse_input_qubits(qubits)
        # Or if it is no string at all, it will raise a failure
        else:
            typer.echo(
                f"Input qubits {qubits} cannot be parsed. Please provide a valid input for --qubits or -q."
            )
            raise typer.Abort()
    except TypeError:
        typer.echo(
            f"Input qubits empty. Please provide a valid input for --qubits or -q."
        )
        raise typer.Abort()

    # Load the default configuration package
    load(template=".default")

    # Create a configuration package object for easier handling
    configuration_package = ConfigurationPackage.from_toml(
        os.path.join(ENV.config_dir, "configuration.meta.toml")
    )

    # Insert the template values for device configuration
    configs_to_update = ["device_config", "run_config"]

    # Iterate over the configurations to update
    # Note: This can be looped at the moment, since there is a very simple logic behind updating
    #       the configurations. It can also be solved in a more advanced way and more specific for
    #       each single configuration file, but right now the only necessary parameter is the list
    #       of qubits.
    for config_name in configs_to_update:

        # Get the path to the configuration template
        config_template_path = os.path.join(
            configuration_package.misc_filepaths["j2_templates"],
            f"{config_name}.j2",
        )
        # Read the template file content
        with open(config_template_path, "r") as file:
            template_content = file.read()

        # Create a Template object
        template = Template(template_content)

        # Insert the template values for run configuration
        output = template.render(qubits=qubits_)

        # Write the configuration values to the .toml files
        config_output_file_path = configuration_package.config_files[config_name]

        # Write the output to a TOML file
        with open(config_output_file_path, "w") as toml_file:
            toml_file.write(output)


@cli.command(help="Open the dataset browser (quantifiles).")
def browser(
    datadir: Annotated[
        str,
        typer.Option(
            "--datadir",
            help="Path to the data directory with your measurement results.",
        ),
    ] = None,
    liveplotting: Annotated[
        bool,
        typer.Option(
            "--liveplotting",
            is_flag=True,
            help="Whether plots should be updated live during measurements.",
        ),
    ] = False,
    log_level: Annotated[
        int,
        typer.Option(
            "--log-level",
            help="Sets the log level of the application.",
        ),
    ] = 30,
):
    """
    This is to open the quantifiles databrowser.
    This endpoint is essentially just a wrapper for the `quantifiles` endpoint.

    Args:
        datadir: Path to the data directory with your measurement results.
        liveplotting: Whether plots should be updated live during measurements.
        log_level: Sets the log level of the application. This is implemented with Python `logging`.

    Returns:

    """
    from tergite_autocalibration.tools.quantifiles import quantifiles

    quantifiles(datadir, liveplotting, log_level)


@cli.command(help="Tell a joke.")
def joke():
    import asyncio
    from jokeapi import Jokes

    async def print_joke():
        j = await Jokes()  # Initialise the class
        joke_ = await j.get_joke(
            blacklist=["racist", "religious", "political", "nsfw", "sexist"]
        )  # Retrieve a random joke
        if joke_["type"] == "single":  # Print the joke
            typer.echo(joke_["joke"])
        else:
            typer.echo(joke_["setup"])
            typer.echo(joke_["delivery"])

    asyncio.run(print_joke())
