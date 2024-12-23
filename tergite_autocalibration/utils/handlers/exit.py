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

import sys

from tergite_autocalibration.utils.logging import logger


def exit_handler():
    """
    Cleanup actions on exit of the autocalibration
    """

    # Retrieve whether the program is crashing or terminated normally
    exc_type, exc_value, _ = sys.exc_info()

    # This is the normal case when the program just terminates
    if exc_type is None:
        logger.status("Autocalibration terminated successfully. Goodbye.")

    # This is the case where the program got interrupted by the user
    elif exc_type is KeyboardInterrupt:
        logger.status("Autocalibration exited due to user interruption (Ctrl+C).")

    # This is the case whenever the program crashed
    else:
        logger.error(
            f"Autocalibration exited due to an exception: {exc_type.__name__}: {exc_value}"
        )
