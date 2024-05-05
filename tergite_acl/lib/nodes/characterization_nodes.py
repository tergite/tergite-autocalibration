from time import sleep

import numpy as np

from tergite_acl.lib.analysis.T1_analysis import T1Analysis, T2Analysis, T2EchoAnalysis
from tergite_acl.lib.analysis.check_cliffords_analysis import CheckCliffordsAnalysis
from tergite_acl.lib.analysis.all_XY_analysis import All_XY_Analysis
# from analysis.cz_chevron_analysis import CZChevronAnalysis, CZChevronAnalysisReset
from tergite_acl.lib.analysis.randomized_benchmarking_analysis import RandomizedBenchmarkingAnalysis
from tergite_acl.lib.node_base import BaseNode
from tergite_acl.lib.calibration_schedules.T1 import T1, T2, T2Echo
from tergite_acl.lib.calibration_schedules.check_cliffords import Check_Cliffords
from tergite_acl.lib.calibration_schedules.randomized_benchmarking import Randomized_Benchmarking
from tergite_acl.lib.calibration_schedules.all_XY import All_XY


class All_XY_Node(BaseNode):
    measurement_obj = All_XY
    analysis_obj = All_XY_Analysis

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.all_qubits = all_qubits
        self.redis_field = ['error_syndromes']
        self.backup = False

    @property
    def dimensions(self):
        return (len(self.samplespace['delays'][self.all_qubits[0]]), 1)

    @property
    def samplespace(self):
        cluster_samplespace = {
            'delays': {qubit: 8e-9 + np.arange(0, 300e-6, 6e-6) for qubit in self.all_qubits}
        }
        return cluster_samplespace


class T1_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.all_qubits = all_qubits
        self.redis_field = ['t1_time']
        self.measurement_obj = T1
        self.analysis_obj = T1Analysis
        self.backup = False

        self.type = 'parameterized_simple_sweep'
        self.node_externals = range(2)
        self.external_parameter_name = 'repeat'
        self.external_parameter_value = 0

        self.sleep_time = 3
        self.operations_args = []

    def pre_measurement_operation(self, external=1):
        if external > 0:
            print(f'sleeping for {self.sleep_time} seconds')
            sleep(self.sleep_time)

    @property
    def dimensions(self):
        return (len(self.samplespace['delays'][self.all_qubits[0]]), 1)

    @property
    def samplespace(self):
        cluster_samplespace = {
            'delays': {qubit: 8e-9 + np.arange(0, 300e-6, 6e-6) for qubit in self.all_qubits}
        }
        return cluster_samplespace


class Randomized_Benchmarking_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.type = 'parameterized_sweep'
        self.all_qubits = all_qubits
        self.node_dictionary = node_dictionary
        self.backup = False
        self.redis_field = ['fidelity']
        self.measurement_obj = Randomized_Benchmarking
        self.analysis_obj = RandomizedBenchmarkingAnalysis

        # TODO change it a dictionary like samplespace
        self.node_externals = 6 * np.arange(5, dtype=np.int32)
        self.external_parameter_name = 'seed'
        self.external_parameter_value = 0
        ####################

    @property
    def dimensions(self):
        return (len(self.samplespace['number_of_cliffords'][self.all_qubits[0]]), 1)

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
            'number_of_cliffords': {
                # qubit: all_numbers for qubit in self.all_qubits
                # qubit: np.array([2, 16, 128, 256,512, 768, 1024, 0, 1]) for qubit in self.all_qubits
                qubit: np.array([2, 16, 128, 256, 512, 768, 1024, 0, 1]) for qubit in self.all_qubits
            },
        }
        return cluster_samplespace


class Check_Cliffords_Node:
    def __init__(self, name: str, all_qubits: list[str], **kwargs):
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = kwargs
        self.redis_field = ['t1_time']  # TODO Empty?
        self.measurement_obj = Check_Cliffords
        self.analysis_obj = CheckCliffordsAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'clifford_indices': {
                qubit: np.linspace(0, 25) for qubit in self.all_qubits
            }
        }
        return cluster_samplespace


class T2_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.redis_field = ['t2_time']
        self.qubit_state = 0
        self.measurement_obj = T2
        self.analysis_obj = T2Analysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'delays': {qubit: 8e-9 + np.arange(0, 100e-6, 1e-6) for qubit in self.all_qubits}
        }
        return cluster_samplespace


class T2_Echo_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.redis_field = ['t2_time']
        self.qubit_state = 0
        self.measurement_obj = T2Echo
        self.analysis_obj = T2EchoAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'delays': {qubit: 8e-9 + np.arange(0, 300e-6, 6e-6) for qubit in self.all_qubits}
        }
        return cluster_samplespace
