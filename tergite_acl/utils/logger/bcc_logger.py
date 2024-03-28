# This code is part of Tergite
#
# (C) Copyright David Wahlstedt 2022
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
#
# Modified:
#
# - Martin Ahindura 2023

"""Utilities for logging"""
import logging


def get_logger():
    """Retrieves the default logger"""
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
    )
    # The following two lines are not used yet, but can be good to have available:
    logger.setLevel(logging.INFO)
    return logger
