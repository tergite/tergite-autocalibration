import numpy as np

from .analysis import PurityBenchmarkingAnalysis
from .measurement import PurityBenchmarking
from ....utils.node_subclasses import ParametrizedSweepNode


class Purity_Benchmarking_Node(ParametrizedSweepNode):
    measurement_obj = PurityBenchmarking
    analysis_obj = PurityBenchmarkingAnalysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.type = "parameterized_sweep"
        self.all_qubits = all_qubits
        self.schedule_keywords = schedule_keywords
        self.backup = False
        self.redis_field = ["purity_fidelity"]
        self.schedule_keywords = {}

        self.initial_schedule_samplespace = {
            "number_of_cliffords": {
                # qubit: all_numbers for qubit in self.all_qubits
                # qubit: np.array([2, 16, 128, 256,512, 768, 1024, 0, 1]) for qubit in self.all_qubits
                qubit: np.array([0, 2, 4, 8, 16, 128, 256, 512, 1024, 0, 1, 2, 0, 2, 4, 8, 16, 128, 256, 512, 1024, 0, 2, 4, 8, 16, 128, 256, 512, 1024])
                for qubit in self.all_qubits
            },
        }

        self.external_samplespace = {
            "seeds": {qubit: np.arange(5, dtype=np.int32) for qubit in self.all_qubits}
        }

    def pre_measurement_operation(self, reduced_ext_space: dict):
        self.schedule_samplespace = (
            self.initial_schedule_samplespace | reduced_ext_space
        )