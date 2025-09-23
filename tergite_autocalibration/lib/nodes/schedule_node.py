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

from quantify_scheduler.instrument_coordinator.utility import xarray

from tergite_autocalibration.lib.base.node_interface import MeasurementType


class ScheduleNode(MeasurementType):
    def measure_node(self, cluster_status, node) -> xarray.Dataset:
        """
        Measurements that involve only schedule parametres
        """
        compiled_schedule = node.precompile(node.schedule_samplespace)
        result_dataset = node.measure_compiled_schedule(
            compiled_schedule,
            cluster_status=cluster_status,
        )
        return result_dataset


class OuterScheduleNode(MeasurementType):
    @property
    def outer_schedule_dimensions(self) -> int:
        """
        size of outer samplespace E.g. in
        self.outer_samplespace = {
            'cz_amplitudes': {'q06_q07': np.array([1e-6, 2e-6, 3e-6, 4e-6])}
        }
        the external_dimensions is 4
        """
        outer_settable_quantities = self.outer_schedule_samplespace.keys()

        if len(outer_settable_quantities) > 1:
            raise NotImplementedError("Multidimensional Outer Samplespace")

        settable = list(outer_settable_quantities)[0]
        measured_elements = self.outer_schedule_samplespace[settable].keys()
        first_element = list(measured_elements)[0]

        dimensions = len(self.outer_schedule_samplespace[settable][first_element])
        return dimensions

    def measure_node(self, cluster_status) -> xarray.Dataset:
        """
        This correspond to schedules where the measurement points
        are more than the memory limit of the QRM_RF.
        For example large single shots measurements
        """
        iterations = self.outer_schedule_dimensions
        outer_dim = list(self.outer_schedule_samplespace.keys())[0]

        result_dataset = xarray.Dataset()

        for current_iteration in range(iterations):
            reduced_outer_samplespace = reduce_samplespace(
                current_iteration, self.outer_schedule_samplespace
            )
            element_dict = list(reduced_outer_samplespace.values())[0]
            current_value = list(element_dict.values())[0]

            samplespace = self.schedule_samplespace | reduced_outer_samplespace
            compiled_schedule = self.precompile(samplespace)

            ds = self.measure_compiled_schedule(
                compiled_schedule,
                cluster_status,
                measurement=(current_iteration, iterations),
            )
            ds = ds.expand_dims({outer_dim: np.array([current_value])})
            result_dataset = xarray.merge([ds, result_dataset])

        return result_dataset
