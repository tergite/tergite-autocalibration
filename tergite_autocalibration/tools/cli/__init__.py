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

from typing import Annotated

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
def quickstart():
    """
    Runs the quickstart and set up the autocalibration with reasonable default values.
    This is to some extent similar to `acli config load -t .default`, but additionally sets up the .env file.

    Returns:

    """
    from .config import load

    load(template=".default")


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
