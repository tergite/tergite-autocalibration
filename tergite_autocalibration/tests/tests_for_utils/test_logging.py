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

from tergite_autocalibration.tests.utils.decorators import preserve_os_env
from tergite_autocalibration.utils.logging.decorators import is_logging_suppressed


@preserve_os_env
def test_suppress_logging_true():
    """
    Check whether logging is suppressed
    """

    os.environ["SUPPRESS_LOGGING"] = "True"
    assert is_logging_suppressed() is True


@preserve_os_env
def test_suppress_logging_false():
    """
    Check whether logging is not suppressed
    """
    assert is_logging_suppressed() is False
