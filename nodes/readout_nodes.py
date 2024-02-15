import numpy as np
import redis
from calibration_schedules.resonator_spectroscopy import Resonator_Spectroscopy
from calibration_schedules.punchout import Punchout
from calibration_schedules.ro_frequency_optimization import RO_frequency_optimization
from calibration_schedules.ro_amplitude_optimization import RO_amplitude_optimization
from calibration_schedules.state_discrimination import Single_Shots_RO
from nodes.base_node import Base_Node

from analysis.resonator_spectroscopy_analysis import (
    ResonatorSpectroscopyAnalysis,
    ResonatorSpectroscopy_1_Analysis,
    ResonatorSpectroscopy_2_Analysis
)
from analysis.optimum_ro_frequency_analysis import (
    OptimalROFrequencyAnalysis,
    OptimalRO_012_FrequencyAnalysis
)
from analysis.optimum_ro_amplitude_analysis import OptimalROAmplitudeAnalysis
from analysis.state_discrimination_analysis import StateDiscriminationAnalysis
from analysis.punchout_analysis import PunchoutAnalysis


from config_files.VNA_LOKIB_values import VNA_resonator_frequencies


class Resonator_Spectroscopy_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['ro_freq', 'Ql', 'resonator_minimum']
        self.measurement_obj = Resonator_Spectroscopy
        self.analysis_obj = ResonatorSpectroscopyAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'ro_frequencies': {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }
        return cluster_samplespace


class Resonator_Spectroscopy_1_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['ro_freq_1', 'Ql_1', 'resonator_minimum_1']
        self.qubit_state = 1
        self.measurement_obj = Resonator_Spectroscopy
        self.analysis_obj = ResonatorSpectroscopy_1_Analysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'ro_frequencies': {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }
        return cluster_samplespace


class Resonator_Spectroscopy_2_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['ro_freq_2']
        self.qubit_state = 2
        self.measurement_obj = Resonator_Spectroscopy
        self.analysis_obj = ResonatorSpectroscopy_2_Analysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'ro_frequencies': {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }
        return cluster_samplespace


class Punchout_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['ro_ampl']
        self.measurement_obj = Punchout
        self.analysis_obj = PunchoutAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'ro_frequencies': {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            },
            'ro_amplitudes': {
                qubit: np.linspace(0.005, 0.022, 8) for qubit in self.all_qubits
            },
        }
        return cluster_samplespace


class RO_frequency_optimization_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['ro_freq_opt']
        self.qubit_state = 0
        self.measurement_obj = RO_frequency_optimization
        self.analysis_obj = OptimalROFrequencyAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'ro_opt_frequencies': {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }
        return cluster_samplespace

class RO_frequency_optimization_gef_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.redis_field = ['ro_freq_opt']
        self.qubit_state = 2
        self.measurement_obj = RO_frequency_optimization
        self.analysis_obj = OptimalRO_012_FrequencyAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'ro_opt_frequencies': {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }
        return cluster_samplespace

class RO_amplitude_optimization_gef_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.redis_field = ['ro_ampl_opt','inv_cm_opt']
        self.qubit_state = 2
        self.measurement_obj = RO_amplitude_optimization
        self.analysis_obj = OptimalROAmplitudeAnalysis
        self.node_dictionary = node_dictionary
        self.node_dictionary['loop_repetitions'] = 128

    @property
    def dimensions(self) -> list:
        '''
        overwriting the dimensions of the Base_Node
        '''
        # assuming that all qubit  have the same dimensions on their samplespace
        first_qubit = self.all_qubits[0]

        ampls = len(self.samplespace['ro_amplitudes'][first_qubit])
        states = self.qubit_state + 1
        loops = self.node_dictionary['loop_repetitions']
        dims = states * loops
        return [ampls, dims]


    @property
    def samplespace(self):
        '''
        we write down the 'qubit_states' here to make easier the
        configuration of the raw dataset
        '''
        loops = self.node_dictionary['loop_repetitions']
        cluster_samplespace = {
            'ro_amplitudes': {qubit : np.linspace(0.001,0.121,31) for qubit in self.all_qubits},

            'qubit_states': {
                qubit: np.repeat(np.array([0,1,2], dtype=np.int16), loops)  for qubit in self.all_qubits
            }
        }
        return cluster_samplespace

