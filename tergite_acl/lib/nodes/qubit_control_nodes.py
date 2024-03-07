import numpy as np

from tergite_acl.lib.analysis.motzoi_analysis import MotzoiAnalysis
from tergite_acl.lib.analysis.n_rabi_analysis import NRabiAnalysis
from tergite_acl.lib.analysis.qubit_spectroscopy_analysis import QubitSpectroscopyAnalysis
from tergite_acl.lib.analysis.qubit_spectroscopy_multidim import QubitSpectroscopyMultidim
from tergite_acl.lib.analysis.rabi_analysis import RabiAnalysis
from tergite_acl.lib.analysis.ramsey_analysis import RamseyAnalysis
from tergite_acl.lib.node_base import BaseNode
from tergite_acl.lib.nodes.node_utils import qubit_samples
from tergite_acl.lib.calibration_schedules.motzoi_parameter import Motzoi_parameter
from tergite_acl.lib.calibration_schedules.n_rabi_oscillations import N_Rabi_Oscillations
from tergite_acl.lib.calibration_schedules.rabi_oscillations import Rabi_Oscillations
from tergite_acl.lib.calibration_schedules.ramsey_fringes import Ramsey_fringes
# from calibration_schedules.two_tone_multidim import Two_Tones_Multidim
from tergite_acl.lib.calibration_schedules.two_tone_multidim_loop_reversed import Two_Tones_Multidim
from tergite_acl.lib.calibration_schedules.two_tones_spectroscopy import Two_Tones_Spectroscopy


class Qubit_01_Spectroscopy_Pulsed_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.sweep_range = self.node_dictionary.pop("sweep_range", None)
        self.redis_field = ['freq_01']
        self.measurement_obj = Two_Tones_Spectroscopy
        self.analysis_obj = QubitSpectroscopyAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'spec_frequencies': {
                qubit: qubit_samples(qubit, sweep_range=self.sweep_range) for qubit in self.all_qubits
            }
        }
        return cluster_samplespace


class Qubit_01_Spectroscopy_Multidim_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['freq_01',
                            'spec_ampl_optimal']
        self.measurement_obj = Two_Tones_Multidim
        self.analysis_obj = QubitSpectroscopyMultidim

    @property
    def samplespace(self):
        cluster_samplespace = {
            'spec_pulse_amplitudes': {
                qubit: np.linspace(3e-4, 9e-4, 5) for qubit in self.all_qubits
            },
            'spec_frequencies': {
                qubit: qubit_samples(qubit) for qubit in self.all_qubits
            },
        }
        return cluster_samplespace


class Rabi_Oscillations_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['mw_amp180']
        self.measurement_obj = Rabi_Oscillations
        self.analysis_obj = RabiAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'mw_amplitudes': {
                qubit: np.linspace(0.002, 0.80, 101) for qubit in self.all_qubits
            }
        }
        return cluster_samplespace


class Ramsey_Fringes_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['freq_01']
        self.measurement_obj = Ramsey_fringes
        self.analysis_obj = RamseyAnalysis
        self.backup = False
        self.analysis_kwargs = {"redis_field": "freq_01"}

    @property
    def samplespace(self):
        cluster_samplespace = {
            # 'ramsey_fringes': {
            'ramsey_delays': {
                qubit: np.arange(4e-9, 2048e-9, 8 * 8e-9) for qubit in self.all_qubits
            },
            'artificial_detunings': {
                qubit: np.arange(-2.1, 2.1, 0.8) * 1e6 for qubit in self.all_qubits
            },
            # },
        }
        return cluster_samplespace


class Ramsey_Fringes_12_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['freq_12']
        self.qubit_state = 1
        self.measurement_obj = Ramsey_fringes
        self.analysis_obj = RamseyAnalysis
        self.backup = False
        self.analysis_kwargs = {"redis_field": "freq_12"}

    @property
    def samplespace(self):
        cluster_samplespace = {
            'ramsey_delays': {
                qubit: np.arange(4e-9, 2048e-9, 8 * 8e-9) for qubit in self.all_qubits
            },
            'artificial_detunings': {
                qubit: np.arange(-2.1, 2.1, 0.8) * 1e6 for qubit in self.all_qubits
            },
        }
        return cluster_samplespace


class Motzoi_Parameter_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['mw_motzoi']
        self.measurement_obj = Motzoi_parameter
        self.analysis_obj = MotzoiAnalysis
        self.backup = False

    @property
    def samplespace(self):
        cluster_samplespace = {
            'mw_motzois': {qubit: np.linspace(-0.4, 0.4, 61) for qubit in self.all_qubits},
            'X_repetitions': {qubit: np.arange(2, 17, 4) for qubit in self.all_qubits}
        }
        return cluster_samplespace


class N_Rabi_Oscillations_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['mw_amp180']
        self.measurement_obj = N_Rabi_Oscillations
        self.analysis_obj = NRabiAnalysis
        self.backup = False

    @property
    def samplespace(self):
        cluster_samplespace = {
            'mw_amplitudes_sweep': {qubit: np.linspace(-0.1, 0.1, 61) for qubit in self.all_qubits},
            'X_repetitions': {qubit: np.arange(1, 16, 4) for qubit in self.all_qubits}
        }
        return cluster_samplespace


class Qubit_12_Spectroscopy_Pulsed_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.sweep_range = self.node_dictionary.pop("sweep_range", None)
        self.redis_field = ['freq_12']
        self.qubit_state = 1
        self.measurement_obj = Two_Tones_Spectroscopy
        self.analysis_obj = QubitSpectroscopyAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'spec_frequencies': {
                qubit: qubit_samples(qubit, '12', sweep_range=self.sweep_range) for qubit in self.all_qubits
            }
        }
        return cluster_samplespace


class Qubit_12_Spectroscopy_Multidim_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['freq_12',
                            'spec_ampl_12_optimal']
        self.qubit_state = 1
        self.measurement_obj = Two_Tones_Multidim
        self.analysis_obj = QubitSpectroscopyMultidim

    @property
    def samplespace(self):
        cluster_samplespace = {
            'spec_pulse_amplitudes': {
                qubit: np.linspace(5e-4, 9e-4, 5) for qubit in self.all_qubits
            },
            'spec_frequencies': {
                qubit: qubit_samples(qubit, transition='12') for qubit in self.all_qubits
            },
        }
        return cluster_samplespace


class Rabi_Oscillations_12_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['mw_ef_amp180']
        self.qubit_state = 1
        self.measurement_obj = Rabi_Oscillations
        self.analysis_obj = RabiAnalysis

    @property
    def samplespace(self):
        cluster_samplespace = {
            'mw_amplitudes': {
                qubit: np.linspace(0.002, 0.400, 31) for qubit in self.all_qubits
            }
        }
        return cluster_samplespace
