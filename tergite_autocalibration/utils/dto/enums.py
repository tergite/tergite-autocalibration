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


# Used by check_data to indicate outcome
class DataStatus(Enum):
    in_spec = 1
    out_of_spec = 2
    bad_data = 3
    undefined = 4


# Used to distinguish running on dummy or real clusters
class MeasurementMode(Enum):
    """
    Used to set the cluster mode e.g. dummy cluster or real cluster
    """

    real = 0
    dummy = 1
    re_analyse = 2
