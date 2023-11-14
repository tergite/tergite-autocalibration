import numpy as np
from calibration_schedules.resonator_spectroscopy import Resonator_Spectroscopy
from calibration_schedules.two_tones_spectroscopy import Two_Tones_Spectroscopy
from calibration_schedules.two_tone_multidim import Two_Tones_Multidim
from calibration_schedules.rabi_oscillations import Rabi_Oscillations
from calibration_schedules.T1 import T1
from calibration_schedules.XY_crosstalk import XY_cross
from calibration_schedules.punchout import Punchout
from calibration_schedules.ramsey_fringes import Ramsey_fringes
from calibration_schedules.ro_frequency_optimization import RO_frequency_optimization
from calibration_schedules.ro_amplitude_optimization import RO_amplitude_optimization
from calibration_schedules.state_discrimination import Single_Shots_RO
# from calibration_schedules.drag_amplitude import DRAG_amplitude
from calibration_schedules.motzoi_parameter import Motzoi_parameter
from calibration_schedules.cz_chevron import CZ_chevron

from analysis.motzoi_analysis import MotzoiAnalysis
from analysis.resonator_spectroscopy_analysis import (
    ResonatorSpectroscopyAnalysis,
    ResonatorSpectroscopy_1_Analysis,
    ResonatorSpectroscopy_2_Analysis
)
from analysis.qubit_spectroscopy_analysis import QubitSpectroscopyAnalysis
from analysis.qubit_spectroscopy_multidim import QubitSpectroscopyMultidim
from analysis.optimum_ro_frequency_analysis import (
    OptimalROFrequencyAnalysis,
    OptimalRO_012_FrequencyAnalysis
)
from analysis.optimum_ro_amplitude_analysis import OptimalROAmplitudeAnalysis
from analysis.state_discrimination_analysis import StateDiscrimination
from analysis.rabi_analysis import RabiAnalysis
from analysis.punchout_analysis import PunchoutAnalysis
from analysis.ramsey_analysis import RamseyAnalysis
from analysis.tof_analysis import analyze_tof
from analysis.T1_analysis import T1Analysis
from analysis.coupler_spectroscopy_analysis import CouplerSpectroscopyAnalysis
from analysis.cz_chevron_analysis import CZChevronAnalysis


from config_files.VNA_values import (
    VNA_resonator_frequencies, VNA_qubit_frequencies, VNA_f12_frequencies
)


def resonator_samples(qubit: str) -> np.ndarray:
    res_spec_samples = 91
    sweep_range = 7.0e6
    VNA_frequency = VNA_resonator_frequencies[qubit]
    min_freq = VNA_frequency - sweep_range / 2
    max_freq = VNA_frequency + sweep_range / 2
    return np.linspace(min_freq, max_freq, res_spec_samples)


def qubit_samples(qubit: str, transition: str = '01') -> np.ndarray:
    qub_spec_samples = 85
    sweep_range = 5.0e6
    if transition == '01':
        VNA_frequency = VNA_qubit_frequencies[qubit]
    elif transition == '12':
        VNA_frequency = VNA_f12_frequencies[qubit]
    else:
        raise ValueError('Invalid transition')

    min_freq = VNA_frequency - sweep_range / 2
    max_freq = VNA_frequency + sweep_range / 2
    return np.linspace(min_freq, max_freq, qub_spec_samples)


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
            'rabi_oscillations_12': Rabi_Oscillations_12_Node,
            'resonator_spectroscopy_2': Resonator_Spectroscopy_2_Node,
            'coupler_spectroscopy': Coupler_Spectroscopy_Node,
            'coupler_resonator_spectroscopy': Coupler_Resonator_Spectroscopy_Node,
            'T1': T1_Node,
            'cz_chevron': CZ_Chevron_Node,
            'ro_frequency_optimization': RO_frequency_optimization_Node,
            #'ro_frequency_optimization_gef': RO_frequency_optimization_gef_Node,
        }

    def create_node(self, node_name: str, all_qubits: list[str], ** kwargs):
        print(f'{ kwargs = }')
        node_object = self.node_implementations[node_name](node_name, all_qubits, ** kwargs)
        return node_object


class Base_Node:
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        self.name = name
        self.all_qubits = all_qubits

    def __str__(self):
        return f'Node representation for {self.name} on qubits {self.all_qubits}'

    def __format__(self, message):
        return f'Node representation for {self.name} on qubits {self.all_qubits}'

    def __repr__(self):
        return f'Node({self.name}, {self.all_qubits})'


class Resonator_Spectroscopy_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits)
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = node_dictionary
        self.redis_field = ['ro_freq', 'Ql']
        self.qubit_state = 0
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

class Punchout_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
        super().__init__(name, all_qubits)
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = node_dictionary
        self.redis_field = 'ro_ampl'
        self.qubit_state = 0
        self.measurement_obj = Punchout
        self.analysis_obj = PunchoutAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'ro_frequencies': {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            },
            'ro_amplitudes': {
                qubit: np.linspace(0.005, 0.09, 12) for qubit in self.all_qubits
            },
        }
        return cluster_samplespace

class Qubit_01_Spectroscopy_Pulsed_Node:
    def __init__(self, name: str, all_qubits: list[str], ** kwargs):
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = kwargs
        self.redis_field = ['freq_01']
        self.qubit_state = 0
        self.measurement_obj = Two_Tones_Spectroscopy
        self.analysis_obj = QubitSpectroscopyAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'spec_frequencies': {
                qubit: qubit_samples(qubit) for qubit in self.all_qubits
            }
        }
        return cluster_samplespace

class Qubit_01_Spectroscopy_Multidim_Node:
    def __init__(self, name: str, all_qubits: list[str], ** kwargs):
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = kwargs
        self.redis_field = ['freq_01',
                            'spec_pulse_amplitude']
        self.qubit_state = 0
        self.measurement_obj = Two_Tones_Multidim
        self.analysis_obj = QubitSpectroscopyMultidim

    @property
    def samplespace(self):
        cluster_samplespace = {
            'spec_frequencies': {
                qubit: qubit_samples(qubit) for qubit in self.all_qubits
            },
            'spec_pulse_amplitudes': {
                 qubit: np.linspace(1e-4, 10e-4, 13) for qubit in self.all_qubits
                 #qubit: np.array([1e-4, 3.5e-4, 8e-4]) for qubit in self.all_qubits
            }
        }
        return cluster_samplespace

class Rabi_Oscillations_Node:
    def __init__(self, name: str, all_qubits: list[str], ** kwargs):
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = kwargs
        self.redis_field = ['mw_amp180']
        self.qubit_state = 0
        self.measurement_obj = Rabi_Oscillations
        self.analysis_obj = RabiAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'mw_amplitudes': {
                qubit: np.linspace(0.002, 0.350, 51) for qubit in self.all_qubits
            }
        }
        return cluster_samplespace


class Ramsey_Fringes_Node:
    def __init__(self, name: str, all_qubits: list[str], ** kwargs):
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = kwargs
        self.redis_field = ['freq_01']
        self.qubit_state = 0
        self.measurement_obj = Ramsey_fringes
        self.analysis_obj = RamseyAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'ramsey_correction': {
                'ramsey_delays': {
                    qubit: np.arange(4e-9, 2048e-9, 8 * 8e-9) for qubit in self.all_qubits
                },
                'artificial_detunings': {
                    qubit: np.arange(-2.1, 2.1, 0.8) * 1e6 for qubit in self.all_qubits
                },
            },
        }
        return cluster_samplespace

class T1_Node:
    def __init__(self, name: str, all_qubits: list[str], ** kwargs):
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = kwargs
        self.redis_field = ['t1_time'] # Is this the right redis for T1?
        self.qubit_state = 0
        self.measurement_obj = T1
        self.analysis_obj = T1Analysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'delays': {qubit : np.arange(52e-9,250e-6,4e-6) for qubit in self.all_qubits}
        }
        return cluster_samplespace

class Resonator_Spectroscopy_1_Node:
    def __init__(self, name: str, all_qubits: list[str], ** kwargs):
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = kwargs
        self.redis_field = ['ro_freq_1']
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


class Resonator_Spectroscopy_2_Node:
    def __init__(self, name: str, all_qubits: list[str], ** kwargs):
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = kwargs
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


class Qubit_12_Spectroscopy_Pulsed_Node:
    def __init__(self, name: str, all_qubits: list[str], ** kwargs):
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = kwargs
        self.redis_field = ['freq_12']
        self.qubit_state = 1
        self.measurement_obj = Two_Tones_Spectroscopy
        self.analysis_obj = QubitSpectroscopyAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'spec_frequencies': {
                qubit: qubit_samples(qubit, '12') for qubit in self.all_qubits
            }
        }
        return cluster_samplespace


class Rabi_Oscillations_12_Node:
    def __init__(self, name: str, all_qubits: list[str], ** kwargs):
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = kwargs
        self.redis_field = ['mw_ef_amp180']
        self.qubit_state = 1
        self.measurement_obj = Rabi_Oscillations
        self.analysis_obj = RabiAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'mw_amplitudes': {
                qubit: np.linspace(0.002, 0.500, 55) for qubit in self.all_qubits
            }
        }
        return cluster_samplespace


class RO_frequency_optimization_Node:
    def __init__(self, name: str, all_qubits: list[str], ** kwargs):
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = kwargs
        self.redis_field = 'ro_freq_opt'
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


class CZ_Chevron_Node:
    def __init__(self, name: str, all_qubits: list[str], ** kwargs):
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = kwargs
        self.redis_field = 'cz_pulse_amplitude'
        self.qubit_state = 0
        self.measurement_obj = CZ_chevron
        self.analysis_obj = CZChevronAnalysis
        self.validate()

    def validate(self):
        if 'coupled_qubits' not in self.node_dictionary:
            error_msg = 'coupled_qubits not in job dictionary\n'
            suggestion = 'job dictionary should look like:\n {"coupled_qubits": ["q1","q2"]}'
            raise ValueError(error_msg + suggestion)
        else:
            coupled_qubits = self.node_dictionary['coupled_qubits']
            if len(coupled_qubits) != 2:
                raise ValueError('coupled qubits must be a list with 2 elements')
            elif not all([q in self.all_qubits for q in coupled_qubits]):
                raise ValueError('coupled qubits must be a subset of all calibrated qubits')
            else:
                self.coupled_qubits = coupled_qubits
                self.coupler = coupled_qubits[0] + '_' + coupled_qubits[1]
                self.all_qubits = coupled_qubits

    @property
    def samplespace(self):
        cluster_samplespace = {
            'cz_pulse_frequencies_sweep': {
                qubit: np.linspace(210e6, 250e6, 5) for qubit in self.coupled_qubits
            },
            'cz_pulse_amplitudes': {
                qubit: np.linspace(0.010, 0.05, 7) for qubit in self.coupled_qubits
            },
        }
        return cluster_samplespace

    #     'ro_frequency_optimization_gef': {
    #         'redis_field': 'ro_freq_opt',
    #         'qubit_state': 2,
    #         'measurement_obj': RO_frequency_optimization,
    #         'analysis_obj': OptimalROFrequencyAnalysis
    #     },
class Coupler_Spectroscopy_Node:
    def __init__(self, name: str, all_qubits: list[str], ** kwargs):
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = kwargs
        self.redis_field = 'parking_current'
        self.qubit_state = 0
        # perform 2 tones while biasing the current
        self.measurement_obj = Two_Tones_Spectroscopy
        self.analysis_obj = CouplerSpectroscopyAnalysis
        self.validate()

    def validate(self):
        if 'coupled_qubits' not in self.node_dictionary:
            error_msg = 'coupled_qubits not in job dictionary\n'
            suggestion = 'job dictionary should look like:\n {"coupled_qubits": ["q1","q2"]}'
            raise ValueError(error_msg + suggestion)
        else:
            coupled_qubits = self.node_dictionary['coupled_qubits']
            if len(coupled_qubits) != 2:
                raise ValueError('coupled qubits must be a list with 2 elements')
            elif not all([q in self.all_qubits for q in coupled_qubits]):
                raise ValueError('coupled qubits must be a subset of all calibrated qubits')
            else:
                self.coupled_qubits = coupled_qubits
                self.coupler = coupled_qubits[0] + '_' + coupled_qubits[1]
                self.measurement_qubit = coupled_qubits[0]

    @property
    def samplespace(self):
        qubit = self.measurement_qubit
        cluster_samplespace = {
            'spec_frequencies': {qubit: qubit_samples(qubit)}
        }
        return cluster_samplespace

    @property
    def spi_samplespace(self):
        spi_samplespace = {
            'dc_currents': {self.coupler: np.arange(-3.0e-3, 3.0e-3, 125e-6)},
        }
        return spi_samplespace

class Coupler_Resonator_Spectroscopy_Node:
    def __init__(self, name: str, all_qubits: list[str], ** kwargs):
        self.name = name
        self.all_qubits = all_qubits
        self.node_dictionary = kwargs
        self.redis_field = ['resonator_flux_quantum']
        self.qubit_state = 0
        self.measurement_obj = Resonator_Spectroscopy
        self.analysis_obj = CouplerSpectroscopyAnalysis
        self.validate()

    def validate(self):
        if 'coupled_qubits' not in self.node_dictionary:
            error_msg = 'coupled_qubits not in job dictionary\n'
            suggestion = 'job dictionary should look like:\n {"coupled_qubits": ["q1","q2"]}'
            raise ValueError(error_msg + suggestion)
        else:
            coupled_qubits = self.node_dictionary['coupled_qubits']
            if len(coupled_qubits) != 2:
                raise ValueError('coupled qubits must be a list with 2 elements')
            elif not all([q in self.all_qubits for q in coupled_qubits]):
                raise ValueError('coupled qubits must be a subset of all calibrated qubits')
            else:
                self.coupled_qubits = coupled_qubits
                self.coupler = coupled_qubits[0] + '_' + coupled_qubits[1]
                self.measurement_qubit = coupled_qubits[0]

    @property
    def samplespace(self):
        qubit = self.measurement_qubit
        cluster_samplespace = {
            'ro_frequencies': {qubit: resonator_samples(qubit)}
        }
        return cluster_samplespace

    @property
    def spi_samplespace(self):
        spi_samplespace = {
            'dc_currents': {self.coupler: np.arange(-1.5e-3, 0e-3, 50e-6)},
        }
        return spi_samplespace


    #     'two_tone_multidim': {
    #         'redis_field': 'freq_01',
    #         'qubit_state': 0,
    #         'measurement_obj': Two_Tones_Multidim,
    #         'analysis_obj': QubitSpectroscopyMultidim
    #     },
    #     'ro_amplitude_optimization': {
    #         'redis_field': 'ro_pulse_amp_opt',
    #         'qubit_state': 0,  # doesn't matter
    #         'measurement_obj': RO_amplitude_optimization,
    #         'analysis_obj': OptimalROAmplitudeAnalysis
    #     },
    #     'state_discrimination': {
    #         'redis_field': 'discriminator',
    #         'qubit_state': 0,  # doesn't matter
    #         'measurement_obj': Single_Shots_RO,
    #         'analysis_obj': StateDiscrimination
    #     },
