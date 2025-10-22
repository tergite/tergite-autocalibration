# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024, 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy
from quantify_scheduler.instrument_coordinator.utility import xarray

from tergite_autocalibration.lib.base.node_interface import MeasurementType
from tergite_autocalibration.utils.measurement_utils import (
    reduce_samplespace,
    samplespace_dimensions,
)


class ScheduleNode(MeasurementType):
    def __init__(self, node) -> None:
        self.node = node

    def measure_node(self, measurement_mode) -> xarray.Dataset:
        """
        Simple measurements that involve only schedule parameteres
        """
        compiled_schedule = self.node.precompile(self.node.schedule_samplespace)
        result_dataset = self.node.measure_compiled_schedule(
            compiled_schedule,
            measurement_mode=measurement_mode,
        )
        return result_dataset


class OuterScheduleNode(MeasurementType):

    def measure_node(self, measurement_mode, node) -> xarray.Dataset:
        """
        This correspond to schedules where the measurement points
        exceed the memory limit of the QRM_RF.
        For example large single shots measurements.
        """
        outer_dimensions = samplespace_dimensions(node.outer_schedule_samplespace)
        # this implementation supports only 1 outer parameter
        iterations = outer_dimensions[0]
        outer_dim = list(node.outer_schedule_samplespace.keys())[0]

        result_dataset = xarray.Dataset()

        for this_iteration in range(iterations):
            reduced_outer_samplespace = reduce_samplespace(
                this_iteration, node.outer_schedule_samplespace
            )
            element_dict = list(reduced_outer_samplespace.values())[0]
            current_value = list(element_dict.values())[0]

            samplespace = node.schedule_samplespace | reduced_outer_samplespace
            compiled_schedule = node.precompile(samplespace)

            ds = node.measure_compiled_schedule(
                compiled_schedule,
                measurement_mode,
                measurement=(this_iteration, iterations),
            )
            ds = ds.expand_dims({outer_dim: numpy.array([current_value])})
            result_dataset = xarray.merge([ds, result_dataset])

        return result_dataset
