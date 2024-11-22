# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import os


def is_pytest() -> bool:
    """
    Check whether it is running a pytest

    Returns: True if the application is running as a pytest

    """
    try:
        _ = os.environ["PYTEST_VERSION"]
        return True
    except KeyError:
        return False
