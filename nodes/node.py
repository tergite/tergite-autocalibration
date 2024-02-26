from datetime import time
from time import sleep
import numpy as np
import redis
from calibration_schedules.T1 import T1,T2, T2Echo
from calibration_schedules.state_discrimination import Single_Shots_RO
from calibration_schedules.randomized_benchmarking import Randomized_Benchmarking
from calibration_schedules.check_cliffords import Check_Cliffords
from nodes.base_node import Base_Node

# from calibration_schedules.cz_chevron import CZ_chevron
# from calibration_schedules.cz_chevron_reversed import CZ_chevron, Reset_chevron_dc
from calibration_schedules.cz_chevron_reversed import CZ_chevron
# from calibration_schedules.cz_calibration import CZ_calibration, CZ_calibration_SSRO,CZ_dynamic_phase

from analysis.state_discrimination_analysis import StateDiscriminationAnalysis
from analysis.T1_analysis import T1Analysis, T2Analysis, T2EchoAnalysis

# from analysis.cz_chevron_analysis import CZChevronAnalysis, CZChevronAnalysisReset
# from analysis.cz_calibration_analysis import CZCalibrationAnalysis, CZCalibrationSSROAnalysis
from analysis.randomized_benchmarking_analysis import RandomizedBenchmarkingAnalysis
from analysis.check_cliffords_analysis import CheckCliffordsAnalysis


from config_files.VNA_LOKIB_values import (
    VNA_resonator_frequencies, VNA_qubit_frequencies, VNA_f12_frequencies
)
from nodes.coupler_nodes import (
    CZ_Optimize_Chevron_Node, Coupler_Resonator_Spectroscopy_Node, Coupler_Spectroscopy_Node, CZ_Chevron_Node
)
from nodes.qubit_control_nodes import (
    Motzoi_Parameter_Node,
    N_Rabi_Oscillations_Node,
    Qubit_01_Spectroscopy_Multidim_Node,
    Qubit_01_Spectroscopy_Pulsed_Node,
    Qubit_12_Spectroscopy_Multidim_Node,
    Qubit_12_Spectroscopy_Pulsed_Node,
    Rabi_Oscillations_12_Node,
    Rabi_Oscillations_Node,
    Ramsey_Fringes_12_Node,
    Ramsey_Fringes_Node
)
from nodes.readout_nodes import (
    Punchout_Node,
    RO_amplitude_three_state_optimization_Node,
    RO_amplitude_two_state_optimization_Node,
    RO_frequency_optimization_Node,
    RO_frequency_optimization_gef_Node,
    Resonator_Spectroscopy_1_Node,
    Resonator_Spectroscopy_2_Node,
    Resonator_Spectroscopy_Node
)

redis_connection = redis.Redis(decode_responses=True)

def resonator_samples(qubit: str) -> np.ndarray:
    res_spec_samples = 101
    sweep_range =  2.0e6
    VNA_frequency = VNA_resonator_frequencies[qubit]
    min_freq = VNA_frequency - sweep_range / 2 -0.5e6
    max_freq = VNA_frequency + sweep_range / 2
    return np.linspace(min_freq, max_freq, res_spec_samples)


class NodeFactory:
    def __init__(self):
        self.node_implementations = {
            'punchout': Punchout_Node,
            'resonator_spectroscopy': Resonator_Spectroscopy_Node,
            'qubit_01_spectroscopy_pulsed': Qubit_01_Spectroscopy_Pulsed_Node,
            'qubit_01_spectroscopy_multidim': Qubit_01_Spectroscopy_Multidim_Node,
            'rabi_oscillations': Rabi_Oscillations_Node,
            'ramsey_correction': Ramsey_Fringes_Node,
            'resonator_spectroscopy_1': Resonator_Spectroscopy_1_Node,
            'qubit_12_spectroscopy_pulsed': Qubit_12_Spectroscopy_Pulsed_Node,
            'qubit_12_spectroscopy_multidim': Qubit_12_Spectroscopy_Multidim_Node,
            'rabi_oscillations_12': Rabi_Oscillations_12_Node,
            'ramsey_correction_12': Ramsey_Fringes_12_Node,
            'resonator_spectroscopy_2': Resonator_Spectroscopy_2_Node,
            'motzoi_parameter': Motzoi_Parameter_Node,
            'n_rabi_oscillations': N_Rabi_Oscillations_Node,
            'coupler_spectroscopy': Coupler_Spectroscopy_Node,
            'coupler_resonator_spectroscopy': Coupler_Resonator_Spectroscopy_Node,
            'T1': T1_Node,
            'T2': T2_Node,
            'T2_echo': T2_Echo_Node,
            'reset_chevron': Reset_Chevron_Node,
            'cz_chevron': CZ_Chevron_Node,
            'cz_optimize_chevron': CZ_Optimize_Chevron_Node,
            'cz_calibration': CZ_Calibration_Node,
            'cz_calibration_ssro': CZ_Calibration_SSRO_Node,
            'cz_dynamic_phase': CZ_Dynamic_Phase_Node,
            'ro_frequency_two_state_optimization': RO_frequency_optimization_Node,
            'ro_frequency_three_state_optimization': RO_frequency_optimization_gef_Node,
            'ro_amplitude_two_state_optimization': RO_amplitude_two_state_optimization_Node,
            'ro_amplitude_three_state_optimization': RO_amplitude_three_state_optimization_Node,
            #'ro_frequency_optimization_gef': RO_frequency_optimization_gef_Node,
            'state_discrimination': State_Discrimination_Node,
            'randomized_benchmarking': Randomized_Benchmarking_Node,
            # 'check_cliffords': Check_Cliffords_Node,
        }

    def all_nodes(self):
        return list(self.node_implementations.keys())

    def create_node(self, node_name: str, all_qubits: list[str], ** kwargs):
        node_object = self.node_implementations[node_name](node_name, all_qubits, ** kwargs)
        return node_object

class State_Discrimination_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['discriminator']
        self.measurement_obj = Single_Shots_RO
        self.analysis_obj = StateDiscriminationAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'qubit_states': {
                qubit: np.array(110*[0,0,0,0,1,1,1,1]) for qubit in self.all_qubits
            }
        }
        return cluster_samplespace


class T1_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
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


class Randomized_Benchmarking_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
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
        self.node_externals = 3 * np.arange(3, dtype=np.int32)
        self.external_parameter_name = 'seed'
        self.external_parameter_value = 0
        ####################

    @property
    def dimensions(self):
        return (len(self.samplespace['number_of_cliffords'][self.all_qubits[0]]), 1)

    @property
    def samplespace(self):
        numbers = 2 ** np.arange(1,12,3)
        extra_numbers = [numbers[i] + numbers[i+1] for i in range(len(numbers)-2)]
        extra_numbers = np.array(extra_numbers)
        calibration_points = np.array([0,1])
        all_numbers = np.sort( np.concatenate((numbers, extra_numbers)) )
        # all_numbers = numbers

        all_numbers =  np.concatenate((all_numbers, calibration_points))

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
    def __init__(self, name: str, all_qubits: list[str], ** kwargs):
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = kwargs
        self.redis_field = ['t1_time'] #TODO Empty?
        self.measurement_obj = Check_Cliffords
        self.analysis_obj = CheckCliffordsAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'clifford_indices': {
                qubit: np.linspace(0,25) for qubit in self.all_qubits
            }
        }
        return cluster_samplespace


class T2_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.redis_field = ['t2_time']
        self.qubit_state = 0
        self.measurement_obj = T2
        self.analysis_obj = T2Analysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'delays': {qubit : 8e-9 + np.arange(0,100e-6,1e-6) for qubit in self.all_qubits}
        }
        return cluster_samplespace

class T2_Echo_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.redis_field = ['t2_time']
        self.qubit_state = 0
        self.measurement_obj = T2Echo
        self.analysis_obj = T2EchoAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'delays': {qubit : 8e-9 + np.arange(0,300e-6,6e-6) for qubit in self.all_qubits}
        }
        return cluster_samplespace


class Reset_Chevron_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.all_couplers = couplers
        self.coupler = couplers[0]
        self.redis_field = ['reset_amplitude_qc','reset_duration_qc']
        self.qubit_state = 0
        self.measurement_obj = Reset_chevron_dc
        self.analysis_obj = CZChevronAnalysisReset
        self.coupled_qubits = couplers[0].split(sep='_')
        # print(f'{ self.coupled_qubits = }')

    @property
    def samplespace(self):
        # print(f'{ np.linspace(- 50e6, 50e6, 2) + self.ac_freq = }')
        cluster_samplespace = {
            # Pulse test
            'cz_pulse_durations': {
                qubit: 4e-9+np.linspace(16e-9, 16e-9, 11)  for qubit in self.coupled_qubits
            },
            'cz_pulse_amplitudes': {
                qubit: np.linspace(0.4, 0.4, 11) for qubit in self.coupled_qubits
            },

            # For DC reset
            # 'cz_pulse_durations': {
            #     qubit: 4e-9+np.arange(0e-9, 12*4e-9,4e-9) for qubit in self.coupled_qubits
            # },
            # 'cz_pulse_amplitudes': {
            #     qubit: np.linspace(0.2, 0.8, 61) for qubit in self.coupled_qubits
            # },

            # For AC reset
            # 'cz_pulse_durations': {
            #     qubit: 4e-9+np.arange(0e-9, 36*100e-9,400e-9) for qubit in self.coupled_qubits
            # },
            # 'cz_pulse_frequencies_sweep': {
            #     qubit: np.linspace(210e6, 500e6, 51) + self.ac_freq for qubit in self.coupled_qubits
            # },
        }
        return cluster_samplespace


class CZ_Calibration_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.coupler = couplers[0]
        # print(couplers)
        self.coupled_qubits = couplers[0].split(sep='_')
        # print(self.coupled_qubits)
        # self.node_dictionary = kwargs
        self.redis_field = ['cz_phase','cz_pop_loss']
        self.qubit_state = 2
        self.testing_group = 0 # The edge group to be tested. 0 means all edges.
        self.dynamic = False
        self.measurement_obj = CZ_calibration
        self.analysis_obj = CZCalibrationAnalysis
        # self.validate()

    @property
    def samplespace(self):
        cluster_samplespace = {
            'ramsey_phases': {qubit: np.linspace(0, 360, 31) for qubit in  self.coupled_qubits},
            'control_ons': {qubit: [False,True] for qubit in  self.coupled_qubits},
        }
        return cluster_samplespace

class CZ_Calibration_SSRO_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.coupler = couplers[0]
        self.coupled_qubits = couplers[0].split(sep='_')
        # self.node_dictionary = kwargs
        self.redis_field = ['cz_phase','cz_pop_loss','cz_leakage']
        self.qubit_state = 2
        self.testing_group = 0 # The edge group to be tested. 0 means all edges.
        self.dynamic = False
        self.measurement_obj = CZ_calibration_SSRO
        self.analysis_obj = CZCalibrationSSROAnalysis
        # self.validate()

    @property
    def samplespace(self):
        cluster_samplespace = {
            'control_ons': {qubit: [False,True] for qubit in  self.coupled_qubits},
            'ramsey_phases': {qubit: np.linspace(0, 360, 13) for qubit in  self.coupled_qubits},
            # 'ramsey_phases': {qubit: np.linspace(0.025, 0.025, 1) for qubit in  self.coupled_qubits},
        }
        return cluster_samplespace

class CZ_Dynamic_Phase_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], ** kwargs):
        self.name = name
        self.all_qubits = all_qubits
        self.all_couplers = couplers
        self.node_dictionary = kwargs
        self.coupler = couplers[0]
        # print(couplers)
        self.coupled_qubits = couplers[0].split(sep='_')
        # print(self.coupled_qubits)
        # self.node_dictionary = kwargs
        self.redis_field = ['cz_phase']
        self.qubit_state = 2
        self.testing_group = 0 # The edge group to be tested. 0 means all edges.
        self.dynamic = True
        self.measurement_obj = CZ_dynamic_phase
        self.analysis_obj = CZCalibrationAnalysis
