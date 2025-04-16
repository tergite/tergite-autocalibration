# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Michele Faucci Giannelli 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import abc
from typing import List
import numpy as np
import xarray as xr

from quantify_scheduler.instrument_coordinator.utility import xarray

from tergite_autocalibration.lib.base.node import (
    CouplerNode,
    BaseNode,
    QubitNode,
)
from tergite_autocalibration.utils.measurement_utils import reduce_samplespace
from tergite_autocalibration.utils.logging import logger


class ExternalParameterNode(BaseNode, abc.ABC):
    def pre_measurement_operation(self, reduced_ext_space):
        """
        To be implemented by the child measurement nodes
        """
        pass

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


class ExternalParameterFixedScheduleNode(ExternalParameterNode):
    def __init__(self, name: str, **schedule_keywords):
        super().__init__(name, schedule_keywords=schedule_keywords)

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


class ExternalParameterDifferentSchedulesNode(ExternalParameterNode):
    def __init__(self, name: str, **schedule_keywords):
        super().__init__(name, **schedule_keywords)
        self.external_keywords = {}

    def measure_node(self, cluster_status) -> xarray.Dataset:
        iterations = self.external_dimensions
        external_dim = list(self.external_samplespace.keys())[0]

        result_dataset = xarray.Dataset()
        result_dataset_per_qubit: List[xarray.Dataset] = {}

        # Track remaining iterations per element (could be couplers, qubits, etc.)
        element_iterations = {
            element: len(self.external_samplespace[external_dim][element])
            for element in self.external_samplespace[external_dim].keys()
        }
        logger.info(f"element_iterations: {element_iterations}")
        self.initial_operation()
        max_itarations = max(element_iterations.values())

        for current_iteration in range(max_itarations):
            for external_key in self.external_keywords.keys():

                extracted = self.external_keywords[external_key][current_iteration]
                dic = {external_key: extracted}

                self.schedule_keywords = self.schedule_keywords | dic

            self.reduced_external_samplespace = reduce_samplespace(
                current_iteration, self.external_samplespace
            )
            logger.info(
                f"self.reduced_external_samplespace: {self.reduced_external_samplespace}"
            )

            # Remove elements (e.g., couplers, qubits) that have completed all iterations
            active_elements = [
                element
                for element, remaining in element_iterations.items()
                if remaining > 0
            ]
            logger.info(f"active_elements: {active_elements}")

            # Dynamically update schedule_samplespace with only active elements
            self.schedule_samplespace = {
                param: {
                    qubit: values
                    for qubit, values in elements_dict.items()
                    if any(
                        qubit in active_coupler for active_coupler in active_elements
                    )
                }
                for param, elements_dict in self.schedule_samplespace.items()
            }

            if not self.reduced_external_samplespace[external_dim]:  # Check if empty
                continue  # Skip this iteration if no elements have values left

            element_dict = list(self.reduced_external_samplespace.values())[0]

            if not element_dict:  # Check if empty
                continue  # Skip if no valid values

            # Collect values to expand as coordinates for each active coupler
            coordinate_expansions = {}
            for element in active_elements:
                element_dict = self.reduced_external_samplespace[external_dim]
                if element in element_dict:
                    current_value = element_dict[element]
                    coordinate_expansions[f"{external_dim}_{element}"] = np.array(
                        [current_value]
                    )
                else:
                    continue  # Skip if no value for the current element

            compiled_schedule = self.precompile(self.schedule_samplespace)

            self.pre_measurement_operation(
                reduced_ext_space=self.reduced_external_samplespace
            )

            ds = self.measure_compiled_schedule(
                compiled_schedule,
                cluster_status,
                measurement=(current_iteration, iterations),
            )

            for var_name in ds.data_vars:
                qubit = var_name.removeprefix("y")
                if qubit not in result_dataset_per_qubit:
                    result_dataset_per_qubit[qubit] = xr.Dataset()

                relevant_coords = {
                    coord_name: values
                    for coord_name, values in coordinate_expansions.items()
                    if qubit
                    in coord_name  # qubit 'q08' in 'cz_parking_currents_q08_q09'
                }

                var_data = ds[var_name]
                if relevant_coords:
                    for dim, val in relevant_coords.items():
                        var_data = var_data.expand_dims({dim: val})
                        var_data = var_data.assign_coords({dim: val})

                # Now package it in its own dataset
                var_ds = xr.Dataset({var_name: var_data})

                result_dataset_per_qubit[qubit] = xr.merge(
                    [result_dataset_per_qubit[qubit], var_ds], compat="no_conflicts"
                )

            for var_ds in result_dataset_per_qubit.values():
                result_dataset = xr.merge(
                    [result_dataset, var_ds], compat="no_conflicts"
                )

            for element in active_elements:
                element_iterations[element] -= 1  # Track progress

        # example of final Operation is ramping the current back to 0 in coupler spectroscopy
        self.final_operation()

        return result_dataset


class ExternalParameterFixedScheduleQubitNode(
    ExternalParameterFixedScheduleNode, QubitNode
):
    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super.__init__(self, name, all_qubits, schedule_keywords=schedule_keywords)


class ExternalParameterFixedScheduleCouplerNode(
    ExternalParameterFixedScheduleNode, CouplerNode
):
    def __init__(self, name: str, couplers: list[str], **schedule_keywords):
        CouplerNode.__init__(
            self, name, couplers, schedule_keywords=schedule_keywords
        )


class ExternalParameterDifferentSchedulesCouplerNode(
    ExternalParameterDifferentSchedulesNode, CouplerNode
):
    def __init__(self, name: str, couplers: list[str], **schedule_keywords):
        super().__init__(name, couplers=couplers, **schedule_keywords)
