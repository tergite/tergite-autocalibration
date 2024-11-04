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

from typing import Annotated

import typer

from tergite_autocalibration.lib.utils.node_factory import NodeFactory

node_cli = typer.Typer()

node_factory = NodeFactory()
node_names = node_factory.all_node_names()


def complete_node_name(incomplete: str):
    for node_name in node_names:
        if node_name.startswith(incomplete):
            yield node_name


@node_cli.command(help="Reset all parameters in redis for the node specified.")
def reset(
    name: Annotated[
        str,
        typer.Option(
            "--name",
            "-n",
            help="Name of the node to be reset in redis e.g resonator_spectroscopy.",
            autocompletion=complete_node_name,
        ),
    ] = None,
    all: Annotated[
        bool,
        typer.Option(
            "--all",
            "-a",
            is_flag=True,
            help="Reset all nodes.",
        ),
    ] = False,
    from_node: Annotated[
        str,
        typer.Option(
            "--from-node",
            "-f",
            help="If you want to reset all nodes from specified node in chain.",
            autocompletion=complete_node_name,
        ),
    ] = None,
):
    from tergite_autocalibration.utils.reset_redis_node import ResetRedisNode
    from tergite_autocalibration.lib.utils.graph import range_topological_order
    from tergite_autocalibration.utils.user_input import user_requested_calibration

    topo_order = range_topological_order(
        from_node, user_requested_calibration["target_node"]
    )

    reset_obj_ = ResetRedisNode()
    if from_node:
        if typer.confirm(
            "Do you really want to reset all nodes from"
            + from_node
            + "? It might take some time to recalibrate them."
        ):
            for node in topo_order:
                reset_obj_.reset_node(node)
        else:
            typer.echo("Node reset aborted by user.")
    elif all:
        if typer.confirm(
            "Do you really want to reset all nodes? It might take some time to recalibrate them."
        ):
            reset_obj_.reset_node("all")
        else:
            typer.echo("Node reset aborted by user.")
    elif name is not None:
        reset_obj_.reset_node(name)
    else:
        typer.echo("Please enter a node name or use the -a option to reset all nodes.")
        typer.echo("Please enter a node name or use the -a option to reset all nodes.")
