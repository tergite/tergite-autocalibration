from time import sleep

import numpy as np

from tergite_autocalibration.lib.analysis.T1_analysis import T1Analysis, T2Analysis, T2EchoAnalysis
from tergite_autocalibration.lib.analysis.all_XY_analysis import All_XY_Analysis
# from analysis.cz_chevron_analysis import CZChevronAnalysis, CZChevronAnalysisReset
from tergite_autocalibration.lib.analysis.randomized_benchmarking_analysis import RandomizedBenchmarkingAnalysis
from tergite_autocalibration.lib.base.node import BaseNode
from tergite_autocalibration.lib.base.node_subclasses import ParametrizedSweepNode
from tergite_autocalibration.lib.calibration_schedules.T1 import T1, T2, T2Echo
from tergite_autocalibration.lib.calibration_schedules.randomized_benchmarking import Randomized_Benchmarking
from tergite_autocalibration.lib.calibration_schedules.all_XY import All_XY


class All_XY_Node(BaseNode):
    measurement_obj = All_XY
    analysis_obj = All_XY_Analysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.all_qubits = all_qubits
        self.redis_field = ['error_syndromes']
        self.backup = False
        # TODO properly set the dimensions
        self.schedule_samplespace = {
            'XY_index': {
                qubit: np.array(range(23)) for qubit in self.all_qubits
            }
        }


COHERENCE_REPEATS = 3
RB_REPEATS = 10


class T1_Node(BaseNode):
    measurement_obj = T1
    analysis_obj = T1Analysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.all_qubits = all_qubits
        self.redis_field = ['t1_time']
        self.backup = False

        self.schedule_keywords = {'multiplexing': 'parallel'}  # 'one_by_one' | 'parallel'
        self.number_or_repeated_T1s = 3

        self.sleep_time = 3
        # self.operations_args = []

        self.schedule_samplespace = {
            'delays': {
                qubit: 8e-9 + np.arange(0, 300e-6, 6e-6) for qubit in self.all_qubits
            }
        }
        self.external_samplespace = {
            'repeat': {
                qubit: range(self.number_or_repeated_T1s) for qubit in self.all_qubits
            }
        }

    def pre_measurement_operation(self, reduced_ext_space):
        iteration_dict = reduced_ext_space['repeat']
        # there is some redundancy tha all qubits have the same
        # iteration index, that's why we keep the first value->
        this_iteration = list(iteration_dict.values())[0]
        if this_iteration > 0:
            print(f'sleeping for {self.sleep_time} seconds')
            sleep(self.sleep_time)


class Randomized_Benchmarking_Node(ParametrizedSweepNode):
    measurement_obj = Randomized_Benchmarking
    analysis_obj = RandomizedBenchmarkingAnalysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.type = 'parameterized_sweep'
        self.all_qubits = all_qubits
        self.schedule_keywords = schedule_keywords
        self.backup = False
        self.redis_field = ['fidelity']

        self.initial_schedule_samplespace = {
            'number_of_cliffords': {
                # qubit: all_numbers for qubit in self.all_qubits
                # qubit: np.array([2, 16, 128, 256,512, 768, 1024, 0, 1]) for qubit in self.all_qubits
                qubit: np.array([0, 2, 4, 8, 16, 128, 256, 512, 1024, 0, 1, 2]) for qubit in self.all_qubits
            },
        }

        self.external_samplespace = {
            'seeds': {
                qubit: np.arange(5, dtype=np.int32) for qubit in self.all_qubits
            }
        }

    def pre_measurement_operation(self, reduced_ext_space: dict):
        self.schedule_samplespace = self.initial_schedule_samplespace | reduced_ext_space


# TODO this needs to be reviwed
# class Check_Cliffords_Node:
#     def __init__(self, name: str, all_qubits: list[str], **kwargs):
#         self.name = name
#         self.all_qubits = all_qubits
#         self.schedule_keywords = kwargs
#         self.redis_field = ['t1_time']  # TODO Empty?
#         self.measurement_obj = Check_Cliffords
#         self.analysis_obj = CheckCliffordsAnalysis
#
#     @property
#     def samplespace(self):
#         cluster_samplespace = {
#             'clifford_indices': {
#                 qubit: np.linspace(0, 25) for qubit in self.all_qubits
#             }
#         }
#         return cluster_samplespace

class T2_Node(BaseNode):
    measurement_obj = T2
    analysis_obj = T2Analysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.all_qubits = all_qubits
        self.name = name
        self.redis_field = ['t2_time']
        self.qubit_state = 0
        self.backup = False
        self.type = 'parameterized_simple_sweep'

        self.node_externals = range(COHERENCE_REPEATS)
        self.external_parameter_name = 'repeat'
        self.external_parameter_value = 0

        self.sleep_time = 3
        self.operations_args = []

        self.schedule_samplespace = {
            'delays': {qubit: 8e-9 + np.arange(0, 70e-6, 1e-6) for qubit in self.all_qubits}
        }

    def pre_measurement_operation(self, external=1):
        if external > 0:
            print(f'sleeping for {self.sleep_time} seconds')
            sleep(self.sleep_time)

    @property
    def dimensions(self):
        return (len(self.samplespace['delays'][self.all_qubits[0]]), 1)


class T2_Echo_Node(BaseNode):
    measurement_obj = T2Echo
    analysis_obj = T2EchoAnalysis

    def __init__(self, name: str, all_qubits: list[str], **schedule_keywords):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.all_qubits = all_qubits
        self.name = name
        self.redis_field = ['t2_echo_time']
        self.qubit_state = 0

        self.backup = False
        self.type = 'parameterized_simple_sweep'

        self.node_externals = range(COHERENCE_REPEATS)
        self.external_parameter_name = 'repeat'
        self.external_parameter_value = 0

        self.sleep_time = 3
        self.operations_args = []

        self.schedule_samplespace = {
            'delays': {qubit: 8e-9 + np.array(
                [0, 5, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 100, 120, 140, 160, 200, 240, 280, 320]) * 1e-6 for
                       qubit in self.all_qubits}
        }

    def pre_measurement_operation(self, external=1):
        if external > 0:
            print(f'sleeping for {self.sleep_time} seconds')
            sleep(self.sleep_time)

    @property
    def dimensions(self):
        return (len(self.samplespace['delays'][self.all_qubits[0]]), 1)
