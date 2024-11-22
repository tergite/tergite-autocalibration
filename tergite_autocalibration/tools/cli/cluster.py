# This code is part of Tergite
#
# (C) Copyright Stefan Hill 2024
# (C) Copyright Chalmers Next Labs 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import typer

cluster_cli = typer.Typer()


@cluster_cli.command(help="Reboot the cluster.")
def reboot():
    from qblox_instruments import Cluster
    from tergite_autocalibration.config.globals import CLUSTER_IP

    if typer.confirm(
        "Do you really want to reboot the cluster? This operation can interrupt ongoing measurements."
    ):
        typer.echo(f"Reboot cluster with IP:{CLUSTER_IP}")
        cluster_ = Cluster("cluster", CLUSTER_IP)
        cluster_.reboot()
    else:
        typer.echo("Rebooting cluster aborted by user.")


@cluster_cli.command(help="Prints a list of available clusters.")
def find():
    from qblox_instruments import PlugAndPlay

    with PlugAndPlay() as pnp:
        pnp.print_devices()
