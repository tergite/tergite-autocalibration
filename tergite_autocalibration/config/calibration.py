from typing import List

import toml
from .settings import CALIBRATION_CONFIG


class CalibrationConfig:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CalibrationConfig, cls).__new__(cls)

            calibration_config = toml.load(CALIBRATION_CONFIG)
            cls._target_node = calibration_config["general"]["target_node"]
            cls._qubits = calibration_config["general"]["qubits"]
            cls._couplers = calibration_config["general"]["couplers"]

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


CONFIG = CalibrationConfig()
