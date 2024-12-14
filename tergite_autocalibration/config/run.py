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
    """
    A class to handle all run specific configurations.
    A run is e.g. when you call `acli calibration start` and it is over as soon as the program terminates
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create a run id in the form of YYYY-MM-DD--HH-MM-SS--tac-run-id e.g. 2024-11-27--13-52-10--tac-run-id
        # This can be used e.g. to name output folders
        timestamp_ = datetime.now()
        self._run_id = f"{timestamp_.strftime('%Y-%m-%d--%H-%M-%S')}--tac-run-id"

    @property
    def id(self):
        """
        Returns:
            Run ID

        """
        return self._run_id

    @property
    def target_node(self) -> str:
        """
        Returns:
            Node to calibrate to

        """
        return self._dict["target_node"]

    @property
    def qubits(self) -> List[str]:
        """
        Returns:
            Qubits to be calibrated. This should be a subset or equal the qubits in the device_config.toml

        """
        return self._dict["qubits"]

    @property
    def couplers(self) -> List[str]:
        """
        Returns:
            Coupler to be calibrated. This should be a subset or equal the couplers in the device_config.toml

        """
        return self._dict["couplers"]
