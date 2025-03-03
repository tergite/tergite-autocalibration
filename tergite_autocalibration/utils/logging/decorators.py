# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import os
from functools import wraps

from tergite_autocalibration.utils.misc.types import safe_str_to_bool_int_float


def is_logging_suppressed() -> bool:
    """
    Check whether the logging is suppressed.

    Returns:
        True if it is suppressed, False otherwise.

    """
    suppress_logging_ = os.getenv("SUPPRESS_LOGGING", "False")
    return safe_str_to_bool_int_float(bool, suppress_logging_)


def suppress_logging(fn_):
    """
    This is a decorator to prevent a function from logging.
    """

    @wraps(fn_)
    def wrapper(*args, **kwargs):
        # Temporarily store os variables in a cache
        os.environ["SUPPRESS_LOGGING"] = "True"

        # This is to ensure cases where the decorated function fails
        try:
            result = fn_(*args, **kwargs)

        # Reset environmental variable for the logging
        finally:
            del os.environ["SUPPRESS_LOGGING"]

        # Return the result of the function
        return result

    return wrapper
