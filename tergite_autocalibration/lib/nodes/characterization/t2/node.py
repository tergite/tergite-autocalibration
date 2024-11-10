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

from tergite_autocalibration.lib.nodes.characterization.t2.analysis import (
    T2NodeAnalysis,
    T2EchoNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.characterization.t2.measurement import T2, T2Echo
from tergite_autocalibration.lib.base.node import BaseNode


class T2_Node(BaseNode):
    measurement_obj = T2
    analysis_obj = T2NodeAnalysis
    qubit_qois = ["t2_time"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.all_qubits = all_qubits
        self.backup = False

        self.number_or_repeated_T2s = 1

        self.sleep_time = 3
        # self.operations_args = []

        self.schedule_samplespace = {
            "delays": {
                qubit: 8e-9 + np.arange(0, 70e-6, 1e-6) for qubit in self.all_qubits
            }
        }
        self.external_samplespace = {
            "repeat": {
                qubit: range(self.number_or_repeated_T2s) for qubit in self.all_qubits
            }
        }

    def pre_measurement_operation(self, reduced_ext_space):
        iteration_dict = reduced_ext_space["repeat"]
        # there is some redundancy that all qubits have the same
        # iteration index, that's why we keep the first value->
        this_iteration = list(iteration_dict.values())[0]
        if this_iteration > 0:
            print(f"sleeping for {self.sleep_time} seconds")
            sleep(self.sleep_time)


class T2_Echo_Node(BaseNode):
    measurement_obj = T2Echo
    analysis_obj = T2EchoNodeAnalysis
    qubit_qois = ["t2_echo_time"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.all_qubits = all_qubits
        self.backup = False

        self.number_or_repeated_T2s = 1

        self.sleep_time = 3
        # self.operations_args = []

        self.schedule_samplespace = {
            "delays": {
                qubit: 8e-9 + np.arange(0, 300e-6, 6e-6) for qubit in self.all_qubits
            }
        }
        self.external_samplespace = {
            "repeat": {
                qubit: range(self.number_or_repeated_T2s) for qubit in self.all_qubits
            }
        }

    def pre_measurement_operation(self, reduced_ext_space):
        iteration_dict = reduced_ext_space["repeat"]
        # there is some redundancy that all qubits have the same
        # iteration index, that's why we keep the first value->
        this_iteration = list(iteration_dict.values())[0]
        if this_iteration > 0:
            print(f"sleeping for {self.sleep_time} seconds")
            sleep(self.sleep_time)
