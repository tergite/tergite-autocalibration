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

from pathlib import Path
import click

from tergite_autocalibration.utils.dto.enums import MeasurementMode


@click.group()
def cli():
    pass


@cli.group(help="Handle operations related to the cluster.")
def cluster():
    pass


@cluster.command(help="Reboot the cluster.")
def reboot():
    from qblox_instruments import Cluster
    from tergite_autocalibration.config.settings import CLUSTER_IP

    if click.confirm(
        "Do you really want to reboot the cluster? This operation can interrupt ongoing measurements."
    ):
        click.echo(f"Reboot cluster with IP:{CLUSTER_IP}")
        cluster_ = Cluster("cluster", CLUSTER_IP)
        cluster_.reboot()
    else:
        click.echo("Rebooting cluster aborted by user.")


@cli.group(help="Handle operations related to the node.")
def node():
    pass


@node.command(help="Reset all parameters in redis for the node specified.")
@click.option(
    "-n",
    "--name",
    required=False,
    help="Name of the node to be reset in redis e.g resonator_spectroscopy.",
)
@click.option(
    "-a",
    "--all",
    required=False,
    is_flag=True,
    help="Use -a if you want to reset all nodes.",
)
@click.option(
    "-f",
    "--from_node",
    required=False,
    help="Use -f node_name if you want to reset all nodes from specified node in chain.",
)
def reset(name, all, from_node):
    from tergite_autocalibration.utils.reset_redis_node import ResetRedisNode
    from tergite_autocalibration.lib.utils.graph import range_topological_order
    from tergite_autocalibration.utils.user_input import user_requested_calibration

    topo_order = range_topological_order(
        from_node, user_requested_calibration["target_node"]
    )

    reset_obj_ = ResetRedisNode()
    if from_node:
        if click.confirm(
            "Do you really want to reset all nodes from"
            + from_node
            + "? It might take some time to recalibrate them."
        ):
            for node in topo_order:
                reset_obj_.reset_node(node)
        else:
            click.echo("Node reset aborted by user.")
    elif all:
        if click.confirm(
            "Do you really want to reset all nodes? It might take some time to recalibrate them."
        ):
            reset_obj_.reset_node("all")
        else:
            click.echo("Node reset aborted by user.")
    elif name is not None:
        reset_obj_.reset_node(name)
    else:
        click.echo("Please enter a node name or use the -a option to reset all nodes.")


@cli.group(help="Handle operations related to the calibration graph.")
def graph():
    pass


@graph.command(
    help="Plot the calibration graph to the user specified target node in topological order."
)
def plot():
    from tergite_autocalibration.lib.utils.graph import filtered_topological_order
    from tergite_autocalibration.utils.user_input import user_requested_calibration
    from tergite_autocalibration.utils.visuals import draw_arrow_chart

    n_qubits = len(user_requested_calibration["all_qubits"])
    topo_order = filtered_topological_order(user_requested_calibration["target_node"])
    draw_arrow_chart(f"Qubits: {n_qubits}", topo_order)


@cli.group(help="Handle operations related to the calibration supervisor.")
def calibration():
    pass


@calibration.command(help="Start the calibration supervisor.")
@click.option(
    "-c",
    required=False,
    help="Takes the cluster ip address as argument. If not set, it will try take CLUSTER_IP in the .env file.",
)
@click.option(
    "-r",
    required=False,
    help="Use -r if you want to use rerun an analysis, give the path to the dataset folder (plots will be overwritten), you also need to specify the name of the node using -n",
)
@click.option(
    "-n",
    "--name",
    required=False,
    help="Use to specify the node type to rerun, only works with -r option",
)
@click.option(
    "--push",
    required=False,
    is_flag=True,
    help="If --push the a backend will pushed to an MSS specified in MSS_MACHINE_ROOT_URL in the .env file.",
)
def start(c, d, r, name, push):
    from ipaddress import ip_address, IPv4Address

    from tergite_autocalibration.config.settings import CLUSTER_IP
    from tergite_autocalibration.scripts.calibration_supervisor import (
        CalibrationSupervisor,
    )
    from tergite_autocalibration.scripts.db_backend_update import update_mss

    cluster_mode: "MeasurementMode" = MeasurementMode.real
    parsed_cluster_ip: "IPv4Address" = CLUSTER_IP
    node_name = ""
    data_path = ""

    if r:
        folder_path = Path(r)

        # Check if the folder exists
        if not folder_path.is_dir():
            print(f"Error: The specified folder '{folder_path}' does not exist.")
            exit(1)  # Exit with an error code

        if not name:
            click.echo(
                "You are trying to re-run the analysis on a specific node but you did not specify it."
                "Please specify the node using -n or --name."
            )
            exit(1)  # Exit with an error exit

        cluster_mode = MeasurementMode.re_analyse
        data_path = folder_path
        node_name = name

    # Check whether the ip address of the cluster is set correctly
    if c and not d:
        if len(c) >= 0:
            cluster_mode = MeasurementMode.real
            parsed_cluster_ip = ip_address(c)
        else:
            click.echo(
                "Cluster argument requires the ip address of the cluster as parameter. "
                "Trying to start the calibration supervisor with default cluster configuration."
            )

    supervisor = CalibrationSupervisor(
        cluster_mode=cluster_mode,
        cluster_ip=parsed_cluster_ip,
        node_name=node_name,
        data_path=data_path,
    )
    supervisor.calibrate_system()
    if push:
        update_mss()


@cli.command(help="Handle operations related to the well-being of the user.")
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
