# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Michele Faucci Giannelli 2025
# (C) Copyright Abdullah Al Amin
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

from tergite_autocalibration.lib.base.node_interface import MeasurementType
from tergite_autocalibration.utils.measurement_utils import (
    reduce_samplespace,
    samplespace_dimensions,
)


class ExternalParameterNode(MeasurementType):
    def validate_external_parameter_node(self, node) -> None:
        has_initial = callable(getattr(node, "initial_operation", None))
        has_premeasure = callable(getattr(node, "pre_measurement_operation", None))
        has_final = callable(getattr(node, "final_operation", None))
        if not has_initial:
            raise AttributeError("initial_operation", node)
        if not has_premeasure:
            raise AttributeError("pre_measurement_operation", node)
        if not has_final:
            raise AttributeError("final_operation", node)

    def measure_node(self, measurement_mode, node) -> xarray.Dataset:

        self.validate_external_parameter_node(node)

        external_dimensions = samplespace_dimensions(node.external_samplespace)
        # this implementation supports only 1 external parameter
        iterations = external_dimensions[0]
        external_dim = list(node.external_samplespace.keys())[0]

        result_dataset = xarray.Dataset()

        compiled_schedule = node.precompile(node.schedule_samplespace)

        node.initial_operation()

        for this_iteration in range(iterations):
            node.reduced_external_samplespace = reduce_samplespace(
                this_iteration, node.external_samplespace
            )
            element_dict = list(node.reduced_external_samplespace.values())[0]

            current_value = list(element_dict.values())[0]

            node.pre_measurement_operation(
                reduced_ext_space=node.reduced_external_samplespace
            )

            ds = node.measure_compiled_schedule(
                compiled_schedule,
                measurement_mode,
                measurement=(this_iteration, iterations),
            )

            ds = ds.expand_dims({external_dim: np.array([current_value])})
            result_dataset = xarray.merge([ds, result_dataset])

        # example of final Operation is ramping the current back to 0 in coupler spectroscopy
        node.final_operation()

        return result_dataset
