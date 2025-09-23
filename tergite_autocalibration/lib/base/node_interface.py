# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from __future__ import annotations  # for Node type hint
from abc import ABC, abstractmethod

from colorama import init as colorama_init
import matplotlib
import xarray

from tergite_autocalibration.config.globals import PLOTTING_BACKEND
from tergite_autocalibration.lib.base.analysis import BaseNodeAnalysis
from tergite_autocalibration.lib.base.measurement import BaseMeasurement
from tergite_autocalibration.utils.dto.enums import CalibrationResultStatus

colorama_init()

matplotlib.use(PLOTTING_BACKEND)


class NodeInterface(ABC):
    measurement_obj: BaseMeasurement
    analysis_obj: BaseNodeAnalysis

    @abstractmethod
    def calibrate(self, path, mode) -> CalibrationResultStatus:
        pass

    @abstractmethod
    def measure_node(self, cluster_status) -> xarray.Dataset:
        """
        To be implemented by the Classes that define the Measurement Type:
        ScheduleNode or ExternalParameterNode
        """
        pass

    @abstractmethod
    def post_process(self) -> None:
        pass

    @property
    @abstractmethod
    def dimensions(self) -> list:
        """
        array of dimensions used for raw dataset reshaping
        """
        pass


class MeasurementType(ABC):
    @abstractmethod
    def measure_node(self, cluster_status, node: Node) -> xarray.Dataset:
        pass
