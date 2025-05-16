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

import os.path
from datetime import datetime
from typing import List

from tergite_autocalibration.config.base import TOMLConfigurationFile
from tergite_autocalibration.utils.dto.enums import ApplicationStatus


class RunConfiguration(TOMLConfigurationFile):
    """
    A class to handle all run specific configurations.
    A run is e.g. when you call `acli start` and it is over as soon as the program terminates
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create a run id in the form of YYYY-MM-DD--HH-MM-SS--tac-run-id e.g. 2024-11-27--13-52-10--tac-run-id
        # This can be used e.g. to name output folders
        timestamp_ = datetime.now()
        self._run_id = f"{timestamp_.strftime('%Y-%m-%d--%H-%M-%S')}--tac-run-id"

        # Create a file path in the form of YYYY-MM-DD/"ACTIVE"_HH-MM-SS--target_node

        self._log_dir = os.path.join(
            timestamp_.strftime("%Y-%m-%d"),
            f"{timestamp_.strftime('%H-%M-%S')}_{str(ApplicationStatus.ACTIVE.value)}-{self.target_node}",
        )

        # We need to know the data directory to write the original acquisition date
        self._data_dir = None

    @property
    def id(self):
        """
        Returns:
            Run ID in form of YYYY-MM-DD--HH-MM-SS--"tac-run-id"

        """
        return self._run_id

    @property
    def log_dir(self):
        """
        Returns:
            Run directory in form YYYY-MM-DD/"ACTIVE"_HH-MM-SS--target_node

        """
        return self._log_dir

    @log_dir.setter
    def log_dir(self, value):
        self._log_dir = value

    @property
    def data_dir(self):
        """
        Returns:
            Data directory in form YYYY-MM-DD/"ACTIVE"_HH-MM-SS--target_node

        """
        return self._data_dir

    @data_dir.setter
    def data_dir(self, value):
        self._data_dir = value

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
