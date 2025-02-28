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

import multiprocessing
from pathlib import Path
from typing import Annotated

import typer

calibration_cli = typer.Typer()


@calibration_cli.command(help="Start the calibration supervisor.")
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
            help="Use to specify the node type to rerun, only works with -r option",
        ),
    ] = None,
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
            help="Opens the quantifiles data browser in the background with live plotting enabled.",
        ),
    ] = False,
):
    from ipaddress import ip_address, IPv4Address
    from tergite_autocalibration.tools.quantifiles import quantifiles

    from tergite_autocalibration.config.globals import DATA_DIR
    from tergite_autocalibration.config.globals import CLUSTER_IP
    from tergite_autocalibration.scripts.calibration_supervisor import (
        CalibrationSupervisor,
        CalibrationConfig,
    )
    from tergite_autocalibration.scripts.db_backend_update import update_mss
    from tergite_autocalibration.config.globals import CONFIG
    from tergite_autocalibration.utils.backend.reset_redis_node import ResetRedisNode
    from tergite_autocalibration.utils.dto.enums import MeasurementMode
    from tergite_autocalibration.utils.io.dataset import scrape_and_copy_hdf5_files

    cluster_mode: "MeasurementMode" = MeasurementMode.real
    parsed_cluster_ip: "IPv4Address" = CLUSTER_IP
    target_node_name = CONFIG.run.target_node

    if r:
        cluster_mode = MeasurementMode.re_analyse
        data_to_reanalyse_folder_path = Path(r)

        # Check if the folder exists
        if not data_to_reanalyse_folder_path.is_dir():
            typer.echo(f"Error: The specified folder '{data_to_reanalyse_folder_path}' does not exist.")
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

    # Start the quantifiles dataset browser in the background
    if browser:
        typer.echo("Starting dataset browser...")
        proc = multiprocessing.Process(target=quantifiles, args=(DATA_DIR, True, 30))
        proc.start()

    config = CalibrationConfig(
        cluster_mode=cluster_mode,
        cluster_ip=parsed_cluster_ip,
        target_node_name=target_node_name
    )
    supervisor = CalibrationSupervisor(config)
    supervisor.calibrate_system()

    # Push the results of the calibration to MSS
    if push:
        update_mss()
