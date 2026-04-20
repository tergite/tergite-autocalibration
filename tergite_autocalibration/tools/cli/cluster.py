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

from typing import Annotated

import typer

from tergite_autocalibration.utils.io.parsers import parse_input_qubits
from tergite_autocalibration.utils.logging.decorators import suppress_logging

cluster_cli = typer.Typer()


@cluster_cli.command(help="Reboot the cluster.")
@suppress_logging
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


@cluster_cli.command(
    help="Run the automatic mixer calibration for the current cluster and qubits defined."
)
def mc(
    qubits: Annotated[
        str,
        typer.Option(
            "--qubits",
            "-q",
            help='Qubit input e.g. "q00,q01,q02,q03,q04" or "q01-q05" or "q01-q06, q08". '
            'If the input is an integer e.g. 3, it will generate "q01,q02,q03".',
        ),
    ] = None,
):
    import os

    from tergite_autocalibration.config.globals import CONFIG, ENV
    from tergite_autocalibration.config.package import ConfigurationPackage
    from tergite_autocalibration.tools.mixer_calibration import IQMixerCalibration

    if qubits is None:
        qubits_ = CONFIG.run.qubits
    else:
        qubits_ = parse_input_qubits(qubits)

    if typer.confirm(
        f"Do you really want to run a mixer calibration for qubits {qubits_}? "
        f"This operation will run the mixer calibration for readout and drive lines. "
        f"To run a more customized mixer calibration, please check the documentation for the mixer calibration tool."
    ):
        # Creates a backup of the current configuration in the log directory of the run
        typer.echo(f"Creating backup of configuration package in {CONFIG.run.log_dir}")
        ConfigurationPackage.from_toml(
            os.path.join(ENV.config_dir, "configuration.meta.toml")
        ).copy(str(CONFIG.run.log_dir))
        typer.echo("Backup of configuration package. Done.")

        # calibration qrm-rf modules
        typer.echo("Starting mixer calibration for readout lines.")
        mc_ = IQMixerCalibration(qubits_, "res")
        mc_.calibrate_lo()
        mc_.calibrate_sideband()
        mc_.export_calibration_parameters(overwrite=True, save_to_disk=False)
        typer.echo("Mixer calibration for readout lines. Done.")

        # calibration qcm-rf modules
        typer.echo("Starting mixer calibration for drive lines.")
        mc_ = IQMixerCalibration(qubits_, "mw")
        mc_.calibrate_lo()
        mc_.calibrate_sideband()
        mc_.export_calibration_parameters(overwrite=True, save_to_disk=False)
        typer.echo("Mixer calibration for drive lines. Done.")

    else:
        typer.echo("Mixer calibration aborted by user.")


@cluster_cli.command(help="Reset the mixer calibration for qubits defined.")
def reset_mc(
    qubits: Annotated[
        str,
        typer.Option(
            "--qubits",
            "-q",
            help='Qubit input e.g. "q00,q01,q02,q03,q04" or "q01-q05" or "q01-q06, q08". '
            'If the input is an integer e.g. 3, it will generate "q01,q02,q03".',
        ),
    ] = None,
):
    import os

    from tergite_autocalibration.config.globals import CONFIG, ENV
    from tergite_autocalibration.config.package import ConfigurationPackage
    from tergite_autocalibration.tools.mixer_calibration import IQMixerCalibration

    if qubits is None:
        qubits_ = CONFIG.run.qubits
    else:
        qubits_ = parse_input_qubits(qubits)

    if typer.confirm(
        f"Do you really want to reset the mixer calibration for qubits {qubits_}? "
        f"This operation will reset the mixer calibration for readout and drive lines. "
    ):
        # Creates a backup of the current configuration in the log directory of the run
        typer.echo(f"Creating backup of configuration package in {CONFIG.run.log_dir}")
        ConfigurationPackage.from_toml(
            os.path.join(ENV.config_dir, "configuration.meta.toml")
        ).copy(str(CONFIG.run.log_dir))
        typer.echo("Backup of configuration package. Done.")

        # Creating an object and saving without running the calibration will make it store the default values:
        # {
        #   "dc_offset_i": 0,
        #   "dc_offset_q": 0,
        #   "amp_ratio": 1,
        #   "phase_error": 0
        # }
        mc_ = IQMixerCalibration(qubits_, "res")
        mc_.export_calibration_parameters(overwrite=True, save_to_disk=False)
        mc_ = IQMixerCalibration(qubits_, "mw")
        mc_.export_calibration_parameters(overwrite=True, save_to_disk=False)
        typer.echo("Mixer calibration values reset. Done.")

    else:
        typer.echo("Mixer calibration aborted by user.")


@cluster_cli.command(help="Prints a list of available clusters.")
@suppress_logging
def find():
    from qblox_instruments import PlugAndPlay

    with PlugAndPlay() as pnp:
        pnp.print_devices()
