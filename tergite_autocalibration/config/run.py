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
from datetime import datetime
from typing import List

from tergite_autocalibration.config.base import TOMLConfigurationFile


class RunConfiguration(TOMLConfigurationFile):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        timestamp_ = datetime.now()
        self._run_id = f"{timestamp_.strftime('%Y-%m-%d--%H-%M-%S')}--tac-run-id"

    @property
    def id(self):
        return self._run_id

    @property
    def target_node(self) -> str:
        return self._dict["target_node"]

    @property
    def qubits(self) -> List[str]:
        return self._dict["qubits"]

    @property
    def couplers(self) -> List[str]:
        return self._dict["couplers"]
