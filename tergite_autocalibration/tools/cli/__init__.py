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

import multiprocessing
from pathlib import Path
from typing import Annotated

import typer

from tergite_autocalibration.tools.cli.cluster import cluster_cli
from tergite_autocalibration.tools.cli.config import config_cli
from tergite_autocalibration.tools.cli.graph import graph_cli
from tergite_autocalibration.tools.cli.node import node_cli
from tergite_autocalibration.tools.cli.browser import browser_cli
from tergite_autocalibration.utils.logging.decorators import suppress_logging

cli_kwargs = {"no_args_is_help": True}

cli = typer.Typer(**cli_kwargs, pretty_exceptions_enable=False)

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
    browser_cli,
    **cli_kwargs,
    name="browser",
    help="Manage the data browser.",
)


@cli.command(help="Start the calibration supervisor.")
def start(
    c: Annotated[
        str,
        typer.Option(
            "-c",
            help="Takes the cluster ip address as argument. If not set, it will try take CLUSTER_IP in the .env file.",
        ),
    ] = None,
    d: Annotated[
        bool,
        typer.Option(
            "-d",
            help="Executes the calibration chain in dummy mode.",
        ),
    ] = False,
    r: Annotated[
        str,
        typer.Option(
            "-r",
            help="Use -r if you want to use rerun an analysis, give the path to the dataset folder (plots will be overwritten), you also need to specify the name of the node using -n",
        ),
    ] = None,
    node_name: Annotated[
        str,
        typer.Option(
            "--node-name",
            "-n",
            help="Use --node-name (or -n) to specify the node to run calibration for. If -r is specified, only analysis is run.",
        ),
    ] = None,
    ignore_spec: Annotated[
        bool,
        typer.Option(
            "--ignore-spec",
            help="Use --ignore-spec to force recalibration.",
        ),
    ] = False,
    push: Annotated[
        bool,
        typer.Option(
            "--push",
            is_flag=True,
            help="If --push the a backend will pushed to an MSS specified in MSS_MACHINE_ROOT_URL in the .env file.",
        ),
    ] = False,
    browser: Annotated[
        bool,
        typer.Option(
            "--browser",
            is_flag=True,
            help="Opens the data browser in the background with live plotting enabled.",
        ),
    ] = False,
):
    from ipaddress import ip_address, IPv4Address

    from tergite_autocalibration.config.globals import CLUSTER_IP
    from tergite_autocalibration.scripts.calibration_supervisor import (
        CalibrationSupervisor,
        CalibrationConfig,
    )
    from tergite_autocalibration.scripts.db_backend_update import update_mss
    from tergite_autocalibration.config.globals import CONFIG, ENV
    from tergite_autocalibration.tools.browser import start_browser
    from tergite_autocalibration.utils.backend.reset_redis_node import ResetRedisNode
    from tergite_autocalibration.utils.dto.enums import MeasurementMode
    from tergite_autocalibration.utils.io.dataset import scrape_and_copy_hdf5_files

    cluster_mode: "MeasurementMode" = MeasurementMode.real
    parsed_cluster_ip: "IPv4Address" = CLUSTER_IP
    target_node_name = CONFIG.run.target_node
    CONFIG.run.data_dir = CONFIG.run.log_dir

    if r:
        cluster_mode = MeasurementMode.re_analyse
        data_to_reanalyse_folder_path = Path(r)
        CONFIG.run.data_dir = data_to_reanalyse_folder_path

        # Check if the folder exists
        if not data_to_reanalyse_folder_path.is_dir():
            typer.echo(
                f"Error: The specified folder '{data_to_reanalyse_folder_path}' does not exist."
            )
            exit(1)  # Exit with an error code

        # Check if there is a name specified for the node to be re-analysed
        # Otherwise take it from the run configuration
        if not node_name:
            typer.echo(
                "You are trying to re-run the analysis on a specific node but you did not specify it."
                f"Taking {target_node_name} from run configuration instead."
            )
        else:
            target_node_name = node_name

        # Comfort functionality to reset the re-analysis node first
        if typer.confirm(f"Do you want to reset node {target_node_name}?"):
            if target_node_name is not None:
                ResetRedisNode().reset_node(node_name)

        scrape_and_copy_hdf5_files(data_to_reanalyse_folder_path, CONFIG.run.log_dir)

    # Check whether the ip address of the cluster is set correctly
    if c:
        if len(c) >= 0:
            cluster_mode = MeasurementMode.real
            parsed_cluster_ip = ip_address(c)
        else:
            typer.echo(
                "Cluster argument requires the ip address of the cluster as parameter. "
                "Trying to start the calibration supervisor with default cluster configuration."
            )
    elif d:
        cluster_mode = MeasurementMode.dummy

    # Start the data browser in the background
    if browser:
        typer.echo("Starting data browser...")
        proc = multiprocessing.Process(
            target=start_browser, args=(ENV.data_browser_host, ENV.data_browser_port)
        )
        proc.start()

    config = CalibrationConfig(
        cluster_mode=cluster_mode,
        cluster_ip=parsed_cluster_ip,
        target_node_name=target_node_name,
    )
    supervisor = CalibrationSupervisor(config)
    if cluster_mode is MeasurementMode.re_analyse:
        supervisor.rerun_analysis()
    else:
        supervisor.calibrate_system(node_name=node_name, ignore_spec=ignore_spec)

    # Push the results of the calibration to MSS
    if push:
        update_mss()


cli.add_typer(
    config_cli,
    **cli_kwargs,
    name="config",
    help="Functions related to the configuration.",
)


@cli.command(help="Quickly runs to set reasonable defaults for the configuration.")
@suppress_logging
def quickstart(
    qubits: Annotated[
        str,
        typer.Option(
            "--qubits",
            "-q",
            help='Qubit input e.g. "q00,q01,q02,q03,q04" or "q01-q05" or "q01-q06, q08".'
            'If the input is an integer e.g. 3, it will generate "q01,q02,q03".',
        ),
    ] = None,
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


@cli.command(help="Tell a joke.")
@suppress_logging
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
