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
from enum import Enum
from sys import platform


class OperatingSystem(Enum):
    LINUX = "LINUX"
    MAC = "MAC"
    WINDOWS = "WINDOWS"
    UNDEFINED = "UNDEFINED"


def get_os() -> "OperatingSystem":
    # Safe way to retrieve a string about the operating system
    platform_str: str
    if isinstance(platform, str):
        platform_str = platform.lower()
    else:
        platform_str = platform.system().lower()

    # Return as enum
    if platform_str == "linux":
        return OperatingSystem.LINUX
    elif platform_str == "darwin":
        return OperatingSystem.MAC
    elif "win" in platform_str:
        return OperatingSystem.WINDOWS
    else:
        return OperatingSystem.UNDEFINED
