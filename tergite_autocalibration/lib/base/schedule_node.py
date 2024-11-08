# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
import numpy as np
from quantify_scheduler.instrument_coordinator.utility import xarray

from tergite_autocalibration.lib.base.node import BaseNode
from tergite_autocalibration.lib.utils.validators import (
    MixedSamplespace,
    Samplespace,
    SimpleSamplespace,
    get_batched_dimensions,
    get_number_of_batches,
    reduce_batch,
)
from tergite_autocalibration.utils.measurement_utils import reduce_samplespace


class ScheduleNode(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, schedule_keywords=schedule_keywords)

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
        Measurements that involve only schedule parametres
        """
        result_dataset = self.measure_schedule_node(
            cluster_status=cluster_status,
        )

        return result_dataset

    def measure_schedule_node(
        self,
        cluster_status,
    ) -> xarray.Dataset:

        if self.outer_schedule_samplespace == {}:
            validated_samplespace = Samplespace(self.schedule_samplespace)

            if isinstance(validated_samplespace.root, SimpleSamplespace):
                """
                This correspond to simple cluster schedules
                """
                compiled_schedule = self.precompile(self.schedule_samplespace)
                result_dataset = self.measure_compiled_schedule(
                    compiled_schedule,
                    cluster_status=cluster_status,
                )
            elif isinstance(validated_samplespace.root, MixedSamplespace):
                """
                This correspond to schedules with instructions number
                greater than the instructions limit of the QCM_RF
                """
                batched_schedule_samplespace = self.schedule_samplespace
                number_of_batches = get_number_of_batches(batched_schedule_samplespace)
                batched_dimensions = get_batched_dimensions(
                    batched_schedule_samplespace
                )
                result_dataset = xarray.Dataset(
                    coords={coord: [] for coord in batched_dimensions}
                )
                for batch_index in range(number_of_batches):
                    reduced_schedule_samplespace = reduce_batch(
                        batched_schedule_samplespace, batch_index
                    )
                    self.schedule_samplespace = reduced_schedule_samplespace
                    compiled_schedule = self.precompile(reduced_schedule_samplespace)
                    ds = self.measure_compiled_schedule(
                        compiled_schedule,
                        cluster_status=cluster_status,
                        measurement=(batch_index, number_of_batches),
                    )
                    result_dataset = xarray.combine_by_coords(
                        [result_dataset, ds], data_vars="minimal"
                    )

        else:
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
