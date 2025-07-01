# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Amr Osman 2024
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from time import sleep

import numpy as np

from tergite_autocalibration.lib.nodes.characterization.t1.analysis import (
    T1NodeAnalysis,
)
from tergite_autocalibration.lib.nodes.characterization.t1.measurement import (
    T1Measurement,
)
from tergite_autocalibration.lib.nodes.external_parameter_node import (
    ExternalParameterNode,
)
from tergite_autocalibration.utils.logging import logger


class T1Node(ExternalParameterNode):
    """
    Node for T1 measurement and analysis.
    This node performs T1 measurements on multiple qubits
    and analyzes the results to extract T1 times.
    It uses the T1Measurement class for measurement
    and T1NodeAnalysis for analysis.
    """

    measurement_obj = T1Measurement
    analysis_obj = T1NodeAnalysis
    qubit_qois = ["t1_time"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)

        self.schedule_keywords = {
            "multiplexing": "parallel"
        }  # 'one_by_one' | 'parallel'
        number_of_repeated_t1s = 3
        self.sleep_time = 3

        delays = np.concatenate(
            [
                np.arange(0, 4e-6, 1e-6),  # 4
                np.arange(4e-6, 10e-6, 2e-6),  # 3
                np.arange(10e-6, 40e-6, 5e-6),  # 6
                np.arange(40e-6, 100 - 6, 10e-6),  # 6
                np.arange(100e-6, 200e-6, 20e-6),  # 5
                np.arange(200e-6, 400e-6, 40e-6),  # 5
            ]
        )

        self.schedule_samplespace = {
            "delays": {qubit: 8e-9 + delays for qubit in self.all_qubits}
        }
        self.external_samplespace = {
            "T1_repetitions": {
                qubit: range(number_of_repeated_t1s) for qubit in self.all_qubits
            }
        }

    def pre_measurement_operation(self, reduced_ext_space):
        iteration_dict = reduced_ext_space["T1_repetitions"]
        # there is some redundancy that all qubits have the same
        # iteration index, that's why we keep the first value->
        this_iteration = list(iteration_dict.values())[0]
        if this_iteration > 0:
            logger.info(f"sleeping for {self.sleep_time} seconds")
            sleep(self.sleep_time)
