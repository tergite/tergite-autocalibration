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

import os.path
import signal
import subprocess
import sys
from typing import Annotated

import psutil
import typer

from tergite_autocalibration.utils.logging.decorators import suppress_logging

browser_cli = typer.Typer()

# Global variable to store the process
dash_process = None


@browser_cli.command(help="Start the data browser.")
@suppress_logging
def start(
    host: Annotated[
        str,
        typer.Option(
            "--host",
            "-h",
            help="Set the host for the browser to run, default is 127.0.0.1",
        ),
    ] = None,
    port: Annotated[
        str,
        typer.Option(
            "--port",
            "-p",
            help="Set the port for the browser to run, default is 127.0.0.1",
        ),
    ] = None,
):
    """
    This is to start the data browser.

    Returns:

    """
    from tergite_autocalibration.utils.logging import logger
    from tergite_autocalibration.config.globals import ENV
    from tergite_autocalibration.tools.cli.config.helpers import get_os, OperatingSystem

    # Parse host and load from environment configuration if unspecified
    if host is None:
        host = ENV.data_browser_host

    # Parse port and load from environment configuration if unspecified
    if port is None:
        port = ENV.data_browser_port
    else:
        port = int(port)

    # This is the command that will start the dash app
    start_browser_command = f"from tergite_autocalibration.tools.browser import start_browser; start_browser('{host}', {port})"

    # Start the process (the detaching works differently on different operating systems
    process = None
    if get_os() in [OperatingSystem.LINUX, OperatingSystem.MAC]:
        command = [
            "nohup",
            sys.executable,
            "-c",
            start_browser_command,
            ">",
            "/dev/null",
            "2>&1",
            "&",
        ]
        process = subprocess.Popen(
            command, creationflags=0, startupinfo=None, start_new_session=True
        )
    elif get_os() == OperatingSystem.WINDOWS:
        command = [
            sys.executable,
            "-c",
            start_browser_command,
            ">",
            "nul",
            "2>&1",
        ]
        _startupinfo = subprocess.STARTUPINFO()
        _startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        process = subprocess.Popen(
            command,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            startupinfo=_startupinfo,
            start_new_session=True,
        )

    # Store the pid in a file to later stop the browser
    pid = process.pid
    pid_store_path = os.path.join(ENV.root_dir, ".browser")
    with open(pid_store_path, "w") as f:
        f.write(str(pid))

    logger.status(f"Browser started on http://{host}:{port} with PID {pid}")


@browser_cli.command(help="Stop the data browser.")
@suppress_logging
def stop():
    """
    This is to stop the data browser.

    Returns:

    """
    from tergite_autocalibration.utils.logging import logger
    from tergite_autocalibration.config.globals import ENV

    # Read the pid from the .browser file
    pid_store_path = os.path.join(ENV.root_dir, ".browser")
    with open(pid_store_path, "r") as f:
        pid = int(f.read())

    try:
        # Send termination signal, more gracefully way to stop the process
        os.kill(pid, signal.SIGTERM)
    except psutil.NoSuchProcess:
        logger.error(f"No process found with PID {pid}")
    except psutil.AccessDenied:
        logger.error(f"Permission denied to kill process with PID {pid}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

    logger.status(f"Browser with PID {pid} shut down.")
