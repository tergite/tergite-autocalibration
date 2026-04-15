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

import math
from itertools import product

import numpy
import pandas
from quantify_scheduler.instrument_coordinator.utility import xarray

from tergite_autocalibration.lib.base.measurement import MeasurementType
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
    def __init__(self, node) -> None:
        self.node = node

    def measure_node(self, measurement_mode) -> xarray.Dataset:
        """
        This corresponds to schedules where the measurement points
        exceed the memory limit of the QRM_RF.
        For example large single shots measurements.
        """
        outer_dimensions = samplespace_dimensions(self.node.outer_schedule_samplespace)

        iterations = product(*(range(n) for n in outer_dimensions))
        all_iterations = math.prod(outer_dimensions)
        outer_dim = list(self.node.outer_schedule_samplespace.keys())[0]
        outer_settables = self.node.outer_schedule_samplespace.keys()

        result_dataset = xarray.Dataset()

        for this_interation_index, this_iteration in enumerate(iterations):
            reduced_outer_samplespace = reduce_samplespace(
                this_iteration, self.node.outer_schedule_samplespace
            )
            reduced_outer_dict = {}
            for settable in outer_settables:
                # WARNING: this assumes that the values for all elements are the same at eact iteration
                current_value = list(reduced_outer_samplespace[settable].values())[0]
                reduced_outer_dict[settable] = current_value

            samplespace = self.node.schedule_samplespace | reduced_outer_samplespace
            compiled_schedule = self.node.precompile(samplespace)

            ds = self.node.measure_compiled_schedule(
                compiled_schedule,
                measurement_mode=measurement_mode,
                measurement=(this_interation_index, all_iterations),
            )

            if self.node.name == "cz_calibration":
                # This handles multiindex objects.
                # Example is the cz_calibration node where the outer coordinate
                # is a multiindex object cosisting of frequency and duartion pairs
                current_value_multi_index = pandas.MultiIndex.from_tuples(
                    [current_value], names=["l1", "l2"]
                )
                # current_value = xarray.Coordinates.from_pandas_multiindex(
                #     current_value_multi_index, outer_dim
                # )
                ds = ds.expand_dims({outer_dim: current_value_multi_index})
                ds = ds.assign_coords(
                    {outer_dim: (outer_dim, current_value_multi_index)}
                )
            else:
                for outer_dim in reduced_outer_dict:
                    outer_value = reduced_outer_dict[outer_dim]
                    ds = ds.expand_dims({outer_dim: numpy.array([outer_value])})

            result_dataset = xarray.merge(
                [ds, result_dataset], join="outer", compat="no_conflicts"
            )

        return result_dataset
