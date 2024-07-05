# This code is part of Tergite
#
# (C) Copyright Stefan Hill 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from pathlib import Path

import xarray

from tergite_autocalibration.lib.base.node import BaseNode
from tergite_autocalibration.utils.logger.tac_logger import logger


class ParametrizedSweepNode(BaseNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def calibrate(self, data_path: Path, lab_ic, cluster_status):
        print("Performing parameterized sweep")

        pre_measurement_operation = self.pre_measurement_operation

        # node.external_dimensions is defined in the node_base
        iterations = self.external_dimensions[0]

        result_dataset = xarray.Dataset()

        for current_iteration in range(iterations):
            reduced_external_samplespace = {}
            qubit_values = {}
            external_settable = list(self.external_samplespace.keys())[0]
            # elements may refer to qubits or couplers
            elements = self.external_samplespace[external_settable].keys()
            for element in elements:
                qubit_specific_values = self.external_samplespace[external_settable][
                    element
                ]
                external_value = qubit_specific_values[current_iteration]
                qubit_values[element] = external_value

            reduced_external_samplespace[external_settable] = qubit_values
            self.reduced_external_samplespace = reduced_external_samplespace
            pre_measurement_operation(reduced_ext_space=reduced_external_samplespace)

            compiled_schedule = self.precompile(data_path)

            ds = self.measure_node(
                compiled_schedule,
                lab_ic,
                data_path,
                cluster_status,
            )

            result_dataset = xarray.merge([result_dataset, ds])

        logger.info("measurement completed")
        measurement_result = self.post_process(result_dataset, data_path=data_path)
        logger.info("analysis completed")
        return measurement_result
