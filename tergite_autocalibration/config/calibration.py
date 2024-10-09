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
import importlib.util
import sys
from typing import List

import toml
from .settings import CALIBRATION_CONFIG, USER_SAMPLESPACE


class CalibrationConfig:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CalibrationConfig, cls).__new__(cls)

            calibration_config = toml.load(CALIBRATION_CONFIG)
            cls._target_node = calibration_config["general"]["target_node"]
            cls._qubits = calibration_config["general"]["qubits"]
            cls._couplers = calibration_config["general"]["couplers"]

            us_spec_ = importlib.util.spec_from_file_location(
                "user_samplespace", USER_SAMPLESPACE
            )
            user_samplespace_ = importlib.util.module_from_spec(us_spec_)
            sys.modules["user_samplespace"] = user_samplespace_
            us_spec_.loader.exec_module(user_samplespace_)
            cls._user_samplespace = user_samplespace_.user_samplespace

        return cls._instance

    @property
    def target_node(self) -> str:
        return self._target_node

    @property
    def qubits(self) -> List[str]:
        return self._qubits

    @property
    def couplers(self) -> List[str]:
        return self._couplers

    @property
    def user_samplespace(self):
        return self._user_samplespace


CONFIG = CalibrationConfig()
