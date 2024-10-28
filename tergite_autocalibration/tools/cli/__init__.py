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

import typer

from .calibration import calibration_cli
from .cluster import cluster_cli
from .graph import graph_cli
from .node import node_cli

cli = typer.Typer(no_args_is_help=True)

cli.add_typer(
    calibration_cli,
    name="calibration",
    help="Start the calibration supervisor.",
    no_args_is_help=True,
)
cli.add_typer(
    node_cli,
    name="node",
    help="Handle operations related to the node.",
    no_args_is_help=True,
)
cli.add_typer(
    cluster_cli,
    name="cluster",
    help="Handle operations related to the cluster.",
    no_args_is_help=True,
)
cli.add_typer(
    graph_cli,
    name="graph",
    help="Handle operations related to the calibration graph.",
    no_args_is_help=True,
)


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
            print(joke_["joke"])
        else:
            print(joke_["setup"])
            print(joke_["delivery"])

    asyncio.run(print_joke())
