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

import os.path
from pathlib import Path
from typing import Union

from tergite_autocalibration.config.base import TOMLConfigurationFile
from tergite_autocalibration.tools.cli.calibration import start
from tergite_autocalibration.utils.misc.types import (
    safe_str_to_bool_int_float,
    is_none_str,
)

# Note: This script emulates the cli endpoint `acli calibration start`.
#
#       Before using the script, please read the section about debugging in the documentation
#       carefully. If you are running into any errors, please compare the code in tools/cli
#       to ensure that the code is the same as in the original endpoint.


class DebugConfiguration(TOMLConfigurationFile):
    """
    Configuration to read the debug configuration file for the debugging endpoint.
    """

    @property
    def cluster_ip(self) -> str:
        return self._dict["cluster_ip"]

    @property
    def dummy_cluster(self) -> bool:
        return safe_str_to_bool_int_float(bool, self._dict["dummy_cluster"])

    @property
    def reanalyse(self) -> Union[str, None]:
        return None if is_none_str(self._dict["reanalyse"]) else self._dict["reanalyse"]

    @property
    def node_name(self) -> str:
        return self._dict["node_name"]

    @property
    def push(self):
        return safe_str_to_bool_int_float(bool, self._dict["push"])

    @property
    def browser(self):
        return safe_str_to_bool_int_float(bool, self._dict["browser"])


if __name__ == "__main__":

    debug_config = DebugConfiguration(
        os.path.join(Path(__file__).resolve().parent, "debug.toml")
    )

    start(
        debug_config.cluster_ip,
        debug_config.dummy_cluster,
        debug_config.reanalyse,
        debug_config.node_name,
        debug_config.push,
        debug_config.browser,
    )
