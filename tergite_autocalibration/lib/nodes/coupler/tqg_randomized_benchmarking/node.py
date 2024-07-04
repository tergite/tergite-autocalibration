import numpy as np

from tergite_autocalibration.lib.nodes.characterization.randomized_benchmarking.analysis import (
    RandomizedBenchmarkingAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.tqg_randomized_benchmarking.measurement import (
    TQG_Randomized_Benchmarking,
)
from tergite_autocalibration.lib.utils.node_subclasses import ParametrizedSweepNode

RB_REPEATS = 10


class TQG_Randomized_Benchmarking_Node(ParametrizedSweepNode):
    measurement_obj = TQG_Randomized_Benchmarking
    analysis_obj = RandomizedBenchmarkingAnalysis

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary
    ):
        # TODO: Check this node whether the logic is working
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.type = "parameterized_sweep"
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.coupled_qubits = couplers[0].split(sep="_")
        self.node_dictionary = node_dictionary
        self.backup = False
        self.redis_field = ["tqg_fidelity"]

        self.schedule_samplespace = {
            "number_of_cliffords": {
                # qubit: all_numbers for qubit in self.all_qubits
                qubit: np.array([0, 2, 4, 8, 16, 32, 64, 128, 0, 1, 2])
                for qubit in self.all_qubits
                # qubit: np.array([1, 2,3,4,0, 1]) for qubit in self.all_qubits
            },
        }

        # TODO change it a dictionary like samplespace
        self.node_externals = 42 * np.arange(RB_REPEATS, dtype=np.int32)
        self.external_parameter_name = "seed"
        self.external_parameter_value = 0
        ####################

    @property
    def dimensions(self):
        return (len(self.samplespace["number_of_cliffords"][self.all_qubits[0]]), 1)

    @property
    def samplespace(self):
        numbers = 2 ** np.arange(1, 12, 3)
        extra_numbers = [numbers[i] + numbers[i + 1] for i in range(len(numbers) - 2)]
        extra_numbers = np.array(extra_numbers)
        calibration_points = np.array([0, 1])
        all_numbers = np.sort(np.concatenate((numbers, extra_numbers)))
        # all_numbers = numbers

        all_numbers = np.concatenate((all_numbers, calibration_points))

        # number_of_repetitions = 1

        cluster_samplespace = {
            "number_of_cliffords": {
                # qubit: all_numbers for qubit in self.all_qubits
                qubit: np.array([0, 2, 4, 8, 16, 32, 64, 128, 0, 1, 2])
                for qubit in self.all_qubits
                # qubit: np.array([1, 2,3,4,0, 1]) for qubit in self.all_qubits
            },
        }
        return cluster_samplespace


class TQG_Randomized_Benchmarking_Interleaved_Node(ParametrizedSweepNode):
    measurement_obj = TQG_Randomized_Benchmarking
    analysis_obj = RandomizedBenchmarkingAnalysis

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary
    ):
        # TODO: Check here as well the samplespace and whether it is working as expected
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.type = "parameterized_sweep"
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.coupled_qubits = couplers[0].split(sep="_")
        self.node_dictionary = node_dictionary
        self.backup = False
        self.redis_field = ["tqg_fidelity_interleaved"]
        self.schedule_samplespace = {
            "number_of_cliffords": {
                # qubit: all_numbers for qubit in self.all_qubits
                qubit: np.array([0, 1, 2, 3, 4, 8, 16, 32, 64, 128, 0, 1])
                for qubit in self.all_qubits
                # qubit: np.array([1, 0, 1]) for qubit in self.all_qubits
            },
        }

        self.node_dictionary["interleaving_clifford_id"] = 4386
        # TODO change it a dictionary like samplespace
        self.node_externals = 42 * np.arange(RB_REPEATS, dtype=np.int32)
        self.external_parameter_name = "seed"
        self.external_parameter_value = 0
        ####################

    @property
    def dimensions(self):
        return (len(self.samplespace["number_of_cliffords"][self.all_qubits[0]]), 1)

    @property
    def samplespace(self):
        numbers = 2 ** np.arange(1, 12, 3)
        extra_numbers = [numbers[i] + numbers[i + 1] for i in range(len(numbers) - 2)]
        extra_numbers = np.array(extra_numbers)
        calibration_points = np.array([0, 1])
        all_numbers = np.sort(np.concatenate((numbers, extra_numbers)))
        # all_numbers = numbers

        all_numbers = np.concatenate((all_numbers, calibration_points))

        # number_of_repetitions = 1

        cluster_samplespace = {
            "number_of_cliffords": {
                # qubit: all_numbers for qubit in self.all_qubits
                qubit: np.array([0, 1, 2, 3, 4, 8, 16, 32, 64, 128, 0, 1])
                for qubit in self.all_qubits
                # qubit: np.array([1, 0, 1]) for qubit in self.all_qubits
            },
        }
        return cluster_samplespace
