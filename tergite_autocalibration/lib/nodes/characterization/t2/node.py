# This code is part of Tergite

#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Amr Osman 2024
# (C) Copyright Michele Faucci Giannelli 2024, 2025
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

from tergite_autocalibration.lib.nodes.characterization.t2.analysis import (
    T2EchoNodeAnalysis,
    T2NodeAnalysis,
)
from tergite_autocalibration.lib.nodes.characterization.t2.measurement import (
    T2Measurement,
    T2EchoMeasurement,
)
from tergite_autocalibration.lib.nodes.external_parameter_node import (
    ExternalParameterFixedScheduleQubitNode,
)
from tergite_autocalibration.utils.logging import logger


class T2Node(ExternalParameterFixedScheduleQubitNode):
    """
    Node for T2 measurement and analysis.
    This node performs T2 measurements on multiple qubits
    and analyzes the results to extract T2 times.
    It uses the T2Measurement class for measurement
    and T2NodeAnalysis for analysis.
    """

    measurement_obj = T2Measurement
    analysis_obj = T2NodeAnalysis
    qubit_qois = ["t2_time"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.all_qubits = all_qubits  # Is this needed

        self.number_or_repeated_t2s = 3
        self.sleep_time = 3

        delays = np.arange(0, 150e-6, 5e-6)

        self.schedule_samplespace = {
            "delays": {qubit: 8e-9 + delays for qubit in self.all_qubits}
        }
        self.external_samplespace = {
            "repeat": {
                qubit: range(self.number_or_repeated_t2s) for qubit in self.all_qubits
            }
        }

    def pre_measurement_operation(self, reduced_ext_space):
        iteration_dict = reduced_ext_space["repeat"]
        # there is some redundancy that all qubits have the same
        # iteration index, that's why we keep the first value->
        this_iteration = list(iteration_dict.values())[0]
        if this_iteration > 0:
            logger.info(f"sleeping for {self.sleep_time} seconds")
            sleep(self.sleep_time)


class T2EchoNode(ExternalParameterFixedScheduleQubitNode):
    """
    Node for T2 Echo measurement and analysis.
    This node performs T2 Echo measurements on multiple qubits
    and analyzes the results to extract T2 Echo times.
    It uses the T2EchoMeasurement class for measurement
    and T2EchoNodeAnalysis for analysis.
    """

    measurement_obj = T2EchoMeasurement
    analysis_obj = T2EchoNodeAnalysis
    qubit_qois = ["t2_echo_time"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.all_qubits = all_qubits
        self.backup = False

        self.number_or_repeated_t2s = 3
        self.sleep_time = 3

        delays = np.concatenate(
            [
                np.arange(0, 40e-6, 10e-6),  # 4
                np.arange(40e-6, 100e-6, 20e-6),  # 3
                np.arange(100e-6, 400e-6, 50e-6),  # 6
                np.arange(400e-6, 900e-6, 100e-6),  # 5
                np.arange(900e-6, 1500e-6, 200e-6),  # 3
            ]
        )

        self.schedule_samplespace = {
            "delays": {qubit: 8e-9 + delays for qubit in self.all_qubits}
        }
        self.external_samplespace = {
            "repeat": {
                qubit: range(self.number_or_repeated_t2s) for qubit in self.all_qubits
            }
        }

    def pre_measurement_operation(self, reduced_ext_space):
        iteration_dict = reduced_ext_space["repeat"]
        # there is some redundancy that all qubits have the same
        # iteration index, that's why we keep the first value->
        this_iteration = list(iteration_dict.values())[0]
        if this_iteration > 0:
            logger.info(f"sleeping for {self.sleep_time} seconds")
            sleep(self.sleep_time)
