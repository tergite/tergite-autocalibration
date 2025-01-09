# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs AB 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import os
import sys

from tergite_autocalibration.utils.dto.enums import ApplicationStatus
from tergite_autocalibration.utils.logging import logger


def set_log_dir_exit_status(status_code: "ApplicationStatus"):
    """
    Renames the logdir by changing the status prefix.
    This function should only be called when shutting down the application.
    Otherwise, it could be that logs will end up in a wrong directory.

    Args:
        status_code (ApplicationStatus): The status code of the logdir

    """
    log_dir = logger.log_dir

    # Replace the status code e.g. from ACTIVE to SUCCESS
    new_log_dir = str.replace(
        log_dir, ApplicationStatus.ACTIVE.value, status_code.value
    )

    # Rename the directory for the logs
    os.rename(log_dir, new_log_dir)


def exception_handler(exc_type, exc_value, exc_traceback):
    """
    Handle uncaught exceptions
    """
    logger.error(
        f"Autocalibration exited due to an exception: {exc_type.__name__}: {exc_value}",
        exc_info=(exc_type, exc_value, exc_traceback),
    )
    set_log_dir_exit_status(ApplicationStatus.FAILED)


def exit_handler():
    """
    Cleanup actions on exit of the autocalibration
    """

    # This is the normal case when the program just terminates
    logger.status("Autocalibration terminated. Goodbye.")
    set_log_dir_exit_status(ApplicationStatus.SUCCESS)
