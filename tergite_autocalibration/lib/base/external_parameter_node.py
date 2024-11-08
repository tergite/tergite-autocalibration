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
from tergite_autocalibration.utils.measurement_utils import reduce_samplespace


class ExternalParameterNode(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, schedule_keywords=schedule_keywords)

    @property
    def external_dimensions(self) -> int:
        """
        size of external samplespace E.g. in
        self.external_samplespace = {
            'dc_currents': {'q06_q07': np.array([1e-6, 2e-6, 3e-6, 4e-6])}
        }
        the external_dimensions is 4
        """
        external_settable_quantities = self.external_samplespace.keys()

        if len(external_settable_quantities) > 1:
            raise NotImplementedError("Multidimensional External Samplespace")

        settable = list(external_settable_quantities)[0]
        measured_elements = self.external_samplespace[settable].keys()
        first_element = list(measured_elements)[0]

        dimensions = len(self.external_samplespace[settable][first_element])
        return dimensions

    def measure_node(self, cluster_status) -> xarray.Dataset:
        iterations = self.external_dimensions
        external_dim = list(self.external_samplespace.keys())[0]

        result_dataset = xarray.Dataset()

        compiled_schedule = self.precompile(self.schedule_samplespace)

        self.initial_operation()

        for current_iteration in range(iterations):
            self.reduced_external_samplespace = reduce_samplespace(
                current_iteration, self.external_samplespace
            )
            element_dict = list(self.reduced_external_samplespace.values())[0]
            current_value = list(element_dict.values())[0]

            self.pre_measurement_operation(
                reduced_ext_space=self.reduced_external_samplespace
            )

            ds = self.measure_compiled_schedule(
                compiled_schedule,
                cluster_status,
                measurement=(current_iteration, iterations),
            )

            ds = ds.expand_dims({external_dim: np.array([current_value])})
            result_dataset = xarray.merge([ds, result_dataset])

        # example of final Operation is ramping the current back to 0 in coupler spectroscopy
        self.final_operation()

        return result_dataset
