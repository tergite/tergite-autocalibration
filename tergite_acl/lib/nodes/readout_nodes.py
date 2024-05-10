import numpy as np

from tergite_acl.lib.analysis.optimum_ro_amplitude_analysis import OptimalRO_Three_state_AmplitudeAnalysis, \
    OptimalRO_Two_state_AmplitudeAnalysis
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
    measurement_obj = Resonator_Spectroscopy
    analysis_obj = ResonatorSpectroscopyAnalysis

    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['clock_freqs:readout', 'Ql', 'resonator_minimum']
        self.schedule_samplespace = {
            'ro_frequencies': {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }


class Resonator_Spectroscopy_1_Node(BaseNode):
    measurement_obj = Resonator_Spectroscopy
    analysis_obj = ResonatorSpectroscopy_1_Analysis

    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['extended_clock_freqs:readout_1', 'Ql_1', 'resonator_minimum_1']
        self.qubit_state = 1

        self.schedule_samplespace = {
            'ro_frequencies': {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }


class Resonator_Spectroscopy_2_Node(BaseNode):
    measurement_obj = Resonator_Spectroscopy
    analysis_obj = ResonatorSpectroscopy_2_Analysis

    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['extended_clock_freqs:readout_2']
        self.qubit_state = 2


class Punchout_Node(BaseNode):
    measurement_obj = Punchout
    analysis_obj = PunchoutAnalysis

    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['measure:pulse_amp']

        self.schedule_samplespace = {
            'ro_frequencies': {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            },
            'ro_amplitudes': {
                qubit: np.linspace(0.008, 0.06, 11) for qubit in self.all_qubits
            },
        }


class RO_frequency_optimization_Node(BaseNode):
    measurement_obj = RO_frequency_optimization
    analysis_obj = OptimalROFrequencyAnalysis

    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['extended_clock_freqs:readout_2state_opt']
        self.qubit_state = 0

        self.cluster_samplespace = {
            'ro_frequencies': {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }


class RO_frequency_optimization_gef_Node(BaseNode):
    measurement_obj = RO_frequency_optimization
    analysis_obj = OptimalRO_012_FrequencyAnalysis

    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.redis_field = ['extended_clock_freqs:readout_3state_opt']
        self.qubit_state = 2

        self.cluster_samplespace = {
            'ro_frequencies': {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }


class RO_amplitude_two_state_optimization_Node(BaseNode):
    '''
    TODO the two and three state discrimination is quite similar, they should be merged
    '''
    measurement_obj = RO_amplitude_optimization
    analysis_obj = OptimalRO_Two_state_AmplitudeAnalysis

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
        self.node_dictionary = node_dictionary
        self.node_dictionary['loop_repetitions'] = 1000
        self.plots_per_qubit = 3 #  fidelity plot, IQ shots, confusion matrix

        self.loops = self.node_dictionary['loop_repetitions']

        self.schedule_samplespace = {
            'qubit_states': {
                qubit: np.tile(
                    np.array([0,1], dtype=np.int16), loops
                )  for qubit in self.all_qubits
            },
            'ro_amplitudes': {
                qubit: np.linspace(0.001, 0.01, 11) for qubit in self.all_qubits
            },
        }


class RO_amplitude_three_state_optimization_Node(BaseNode):
    measurement_obj = RO_amplitude_optimization
    analysis_obj = OptimalRO_Three_state_AmplitudeAnalysis

    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.redis_field = ['measure_3state_opt:ro_ampl_3st_opt','inv_cm_opt']
        self.qubit_state = 2
        self.node_dictionary = node_dictionary
        self.node_dictionary['loop_repetitions'] = 1000
        self.plots_per_qubit = 3 #  fidelity plot, IQ shots, confusion matrix
        self.loops = self.node_dictionary['loop_repetitions']

        self.schedule_samplespace = {
            'qubit_states': {
                qubit: np.tile(
                    np.array([0,1,2], dtype=np.int16), self.loops
                )  for qubit in self.all_qubits
            },
            'ro_amplitudes': {
                qubit: np.linspace(0.001, 0.01, 11) for qubit in self.all_qubits
            },
        }
