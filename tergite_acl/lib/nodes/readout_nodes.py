import numpy as np

from tergite_acl.lib.analysis.optimum_ro_amplitude_analysis import OptimalRO_Three_state_AmplitudeAnalysis, \
    OptimalRO_Two_state_AmplitudeAnalysis, OptimalROAmplitudeAnalysis
from tergite_acl.lib.analysis.optimum_ro_frequency_analysis import (
    OptimalROFrequencyAnalysis,
    OptimalRO_012_FrequencyAnalysis
)
from tergite_acl.lib.analysis.punchout_analysis import PunchoutAnalysis
from tergite_acl.lib.analysis.resonator_spectroscopy_analysis import (
    ResonatorSpectroscopyAnalysis,
    ResonatorSpectroscopy_1_Analysis,
    ResonatorSpectroscopy_2_Analysis
)
from tergite_acl.lib.node_base import BaseNode
from tergite_acl.lib.nodes.node_utils import resonator_samples
from tergite_acl.lib.calibration_schedules.punchout import Punchout
from tergite_acl.lib.calibration_schedules.resonator_spectroscopy import Resonator_Spectroscopy
from tergite_acl.lib.calibration_schedules.ro_amplitude_optimization import RO_amplitude_optimization
from tergite_acl.lib.calibration_schedules.ro_frequency_optimization import RO_frequency_optimization


class Resonator_Spectroscopy_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['clock_freqs:readout', 'Ql', 'resonator_minimum']
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


class Resonator_Spectroscopy_1_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['extended_clock_freqs:readout_1', 'Ql_1', 'resonator_minimum_1']
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


class Resonator_Spectroscopy_2_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['extended_clock_freqs:readout_2']
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


class Punchout_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['measure:pulse_amp']
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


class RO_frequency_two_state_optimization_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['extended_clock_freqs:readout_2state_opt']
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

class RO_frequency_three_state_optimization_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.redis_field = ['extended_clock_freqs:readout_3state_opt']
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


class RO_amplitude_two_state_optimization_Node(BaseNode):
    '''
    TODO the two and three state discrimination is quite similar, they should be merged
    '''
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.redis_field = [
            'measure_2state_opt:ro_ampl_2st_opt',
            'measure_2state_opt:rotation',
            'measure_2state_opt:threshold'
        ]
        self.qubit_state = 1
        self.measurement_obj = RO_amplitude_optimization
        self.analysis_obj = OptimalRO_Two_state_AmplitudeAnalysis
        self.node_dictionary = node_dictionary
        self.node_dictionary['loop_repetitions'] = 1000
        self.plots_per_qubit = 3 #  fidelity plot, IQ shots, confusion matrix


    @property
    def samplespace(self):
        '''
        we write down the 'qubit_states' here to make easier the
        configuration of the raw dataset
        '''
        loops = self.node_dictionary['loop_repetitions']
        cluster_samplespace = {
            'qubit_states': {
                qubit: np.tile(np.array([0,1], dtype=np.int16), loops)  for qubit in self.all_qubits
            },
            'ro_amplitudes': {qubit: np.linspace(0.001, 0.01, 11) for qubit in self.all_qubits},

        }
        return cluster_samplespace


class RO_amplitude_three_state_optimization_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.redis_field = ['measure_3state_opt:ro_ampl_3st_opt','inv_cm_opt']
        self.qubit_state = 2
        self.measurement_obj = RO_amplitude_optimization
        self.analysis_obj = OptimalRO_Three_state_AmplitudeAnalysis
        self.node_dictionary = node_dictionary
        self.node_dictionary['loop_repetitions'] = 256
        self.plots_per_qubit = 3 #  fidelity plot, IQ shots, confusion matrix


    @property
    def samplespace(self):
        '''
        we write down the 'qubit_states' here to make easier the
        configuration of the raw dataset
        '''
        loops = self.node_dictionary['loop_repetitions']
        cluster_samplespace = {
            'qubit_states': {
                qubit: np.tile(np.array([0,1,2], dtype=np.int16), loops)  for qubit in self.all_qubits
            },
            'ro_amplitudes': {qubit: np.append(np.linspace(0.001, 0.025, 41),np.linspace(0.026, 0.2, 41)) for qubit in self.all_qubits},

        }
        return cluster_samplespace
