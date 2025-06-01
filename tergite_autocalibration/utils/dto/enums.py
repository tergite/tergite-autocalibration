# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023
# (C) Copyright Stefan Hill 2024
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from enum import Enum


class DataStatus(Enum):
    """
    Used by check_data to indicate outcome
    """

    in_spec = 1
    out_of_spec = 2
    bad_data = 3
    undefined = 4


class NodeType(Enum):
    """
    Qubit or Coupler Node
    """

    qubit_node = 1
    coupler_node = 2


class MeasurementMode(Enum):
    """
    Used to set the cluster mode e.g.  real cluster or re analyse
    """

    real = 0
    dummy = 1
    re_analyse = 2


class ApplicationStatus(Enum):
    """
    Used to check in which state the application is as a whole.
    """

    # The application is just started and running.
    # This is the usual case in the beginning.
    ACTIVE = "ACTIVE"

    # The calibration has finished without software errors.
    # There could be still errors in some analysis functions.
    SUCCESS = "SUCCESS"

    # Some kind of error occurred, the application has stopped.
    FAILED = "FAILED"
