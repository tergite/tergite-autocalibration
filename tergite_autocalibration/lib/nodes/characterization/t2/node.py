from time import sleep

import numpy as np

from .analysis import T2Analysis, T2EchoAnalysis
from .measurement import T2, T2Echo
from ....base.node import BaseNode

COHERENCE_REPEATS = 3

class T2_Node(BaseNode):
    measurement_obj = T2
    analysis_obj = T2Analysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.all_qubits = all_qubits
        self.name = name
        self.redis_field = ["t2_time"]
        self.qubit_state = 0
        self.backup = False
        self.type = "parameterized_simple_sweep"

        self.node_externals = range(COHERENCE_REPEATS)
        self.external_parameter_name = "repeat"
        self.external_parameter_value = 0

        self.sleep_time = 3
        self.operations_args = []

        self.schedule_samplespace = {
            "delays": {
                qubit: 8e-9 + np.arange(0, 70e-6, 1e-6) for qubit in self.all_qubits
            }
        }

    def pre_measurement_operation(self, external=1):
        if external > 0:
            print(f"sleeping for {self.sleep_time} seconds")
            sleep(self.sleep_time)

    @property
    def dimensions(self):
        return (len(self.samplespace["delays"][self.all_qubits[0]]), 1)


class T2_Echo_Node(BaseNode):
    measurement_obj = T2Echo
    analysis_obj = T2EchoAnalysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.all_qubits = all_qubits
        self.name = name
        self.redis_field = ["t2_echo_time"]
        self.qubit_state = 0

        self.backup = False
        self.type = "parameterized_simple_sweep"

        self.node_externals = range(COHERENCE_REPEATS)
        self.external_parameter_name = "repeat"
        self.external_parameter_value = 0

        self.sleep_time = 3
        self.operations_args = []

        self.schedule_samplespace = {
            "delays": {
                qubit: 8e-9
                + np.array(
                    [
                        0,
                        5,
                        10,
                        15,
                        20,
                        25,
                        30,
                        35,
                        40,
                        50,
                        60,
                        70,
                        80,
                        100,
                        120,
                        140,
                        160,
                        200,
                        240,
                        280,
                        320,
                    ]
                )
                * 1e-6
                for qubit in self.all_qubits
            }
        }

    def pre_measurement_operation(self, external=1):
        if external > 0:
            print(f"sleeping for {self.sleep_time} seconds")
            sleep(self.sleep_time)

    @property
    def dimensions(self):
        return (len(self.samplespace["delays"][self.all_qubits[0]]), 1)

