# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Stefan Hill 2024
# (C) Copyright Michele Faucci Giannelli 2024, 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from abc import ABC, abstractmethod

from colorama import init as colorama_init
import matplotlib
import xarray

from tergite_autocalibration.config.globals import PLOTTING_BACKEND
from tergite_autocalibration.lib.base.analysis import BaseNodeAnalysis
from tergite_autocalibration.lib.base.measurement import BaseMeasurement

colorama_init()

matplotlib.use(PLOTTING_BACKEND)


class NodeInterface(ABC):
    measurement_obj: BaseMeasurement
    analysis_obj: BaseNodeAnalysis

    @abstractmethod
    def calibrate(self) -> CalibrationResultStatus:
        pass

    @abstractmethod
    def measure_node(self) -> xarray.Dataset:
        """
        To be implemented by the Classes that define the Measurement Type:
        ScheduleNode or ExternalParameterNode
        """
        pass

    @abstractmethod
    def post_process(self) -> None:
        pass

    @abstractmethod
    def analyze(self) -> dict:
        pass

    @property
    @abstractmethod
    def dimensions(self) -> list:
        """
        array of dimensions used for raw dataset reshaping
        """
        pass
