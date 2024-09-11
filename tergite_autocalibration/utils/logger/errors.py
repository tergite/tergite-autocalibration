# This code is part of Tergite
#
# (C) Copyright Stefan Hill 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


class ClusterNotFoundError(BaseException):
    def __init__(self, msg: str):
        self.__msg = msg

    def __repr__(self):
        return f"ClusterNotFoundError: {self.__msg}"

    def __str__(self):
        return self.__msg
