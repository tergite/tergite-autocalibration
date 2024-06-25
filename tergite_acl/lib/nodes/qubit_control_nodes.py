import numpy as np
from qblox_instruments.qcodes_drivers.cluster import Cluster

from tergite_acl.lib.analysis.adaptive_motzoi_analysis import AdaptiveMotzoiAnalysis
from tergite_acl.lib.analysis.motzoi_analysis import MotzoiAnalysis
from tergite_acl.lib.analysis.n_rabi_analysis import NRabiAnalysis
from tergite_acl.lib.analysis.qubit_spectroscopy_analysis import (
    QubitSpectroscopyAnalysis,
)
from tergite_acl.lib.analysis.qubit_spectroscopy_multidim import (
    QubitSpectroscopyMultidim,
)
from tergite_acl.lib.analysis.rabi_analysis import RabiAnalysis
from tergite_acl.lib.analysis.ramsey_analysis import RamseyAnalysis
from tergite_acl.lib.analysis.ramsey_analysis import RamseyDetuningsAnalysis
from tergite_acl.lib.calibration_schedules.cw_two_nones_spectroscopy import (
    CW_Two_Tones_Spectroscopy,
)
from tergite_acl.lib.calibration_schedules.motzoi_parameter import Motzoi_parameter
from tergite_acl.lib.calibration_schedules.n_rabi_oscillations import (
    N_Rabi_Oscillations,
)
from tergite_acl.lib.calibration_schedules.rabi_oscillations import Rabi_Oscillations
from tergite_acl.lib.calibration_schedules.ramsey_detunings import Ramsey_detunings
from tergite_acl.lib.calibration_schedules.ramsey_fringes import Ramsey_fringes
from tergite_acl.lib.calibration_schedules.two_tone_multidim import Two_Tones_Multidim
from tergite_acl.lib.node_base import BaseNode
from tergite_acl.lib.nodes.node_utils import qubit_samples
from tergite_acl.utils.hardware_utils import set_qubit_LO
from tergite_acl.utils.redis_helper import fetch_redis_params


class Qubit_01_Spectroscopy_Multidim_Node(BaseNode):
    measurement_obj = Two_Tones_Multidim
    analysis_obj = QubitSpectroscopyMultidim

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = [
            'clock_freqs:f01', 'spec:spec_ampl_optimal'
        ]

        self.schedule_samplespace = {
            'spec_pulse_amplitudes': {
                qubit: np.linspace(4e-4, 4e-3, 3) for qubit in self.all_qubits
            },
            'spec_frequencies': {
                qubit: qubit_samples(qubit) for qubit in self.all_qubits
            },
        }


class Rabi_Oscillations_Node(BaseNode):
    measurement_obj = Rabi_Oscillations
    analysis_obj = RabiAnalysis

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['rxy:amp180']
        self.schedule_samplespace = {
            'mw_amplitudes': {
                qubit: np.linspace(0.002, 0.80, 101) for qubit in self.all_qubits
            }
        }


class Ramsey_Fringes_Node(BaseNode):
    measurement_obj = Ramsey_detunings
    analysis_obj = RamseyDetuningsAnalysis

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['clock_freqs:f01']
        self.backup = False
        self.analysis_kwargs = {"redis_field": "clock_freqs:f01"}
        self.schedule_samplespace = {
            'ramsey_delays': {
                qubit: np.arange(4e-9, 2048e-9, 8 * 8e-9) for qubit in self.all_qubits
            },
            'artificial_detunings': {
                qubit: np.arange(-2.1, 2.1, 0.8) * 1e6 for qubit in self.all_qubits
            },
        }


class Ramsey_Fringes_12_Node(BaseNode):
    measurement_obj = Ramsey_detunings
    analysis_obj = RamseyDetuningsAnalysis

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['clock_freqs:f12']
        self.qubit_state = 1
        self.backup = False
        self.analysis_kwargs = {"redis_field": "clock_freqs:f12"}
        self.schedule_samplespace = {
            'ramsey_delays': {
                qubit: np.arange(4e-9, 2048e-9, 8 * 8e-9) for qubit in self.all_qubits
            },
            'artificial_detunings': {
                qubit: np.arange(-2.1, 2.1, 0.8) * 1e6 for qubit in self.all_qubits
            },
        }


class Motzoi_Parameter_Node(BaseNode):
    measurement_obj = Motzoi_parameter
    analysis_obj = MotzoiAnalysis

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['rxy:motzoi']
        self.backup = False
        self.motzoi_minima = []
        self.schedule_samplespace = {
            'mw_motzois': {
                qubit: np.linspace(-0.4, 0.1, 51) for qubit in self.all_qubits
            },
            'X_repetitions': {
                qubit: np.arange(2, 22, 6) for qubit in self.all_qubits
            },
        }


class N_Rabi_Oscillations_Node(BaseNode):
    measurement_obj = N_Rabi_Oscillations
    analysis_obj = NRabiAnalysis

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['rxy:amp180']
        self.backup = False

        self.schedule_samplespace = {
            'mw_amplitudes_sweep': {
                qubit: np.linspace(-0.045, 0.045, 40) for qubit in self.all_qubits
            },
            'X_repetitions': {
                qubit: np.arange(1, 40, 8) for qubit in self.all_qubits
            },
        }


class Qubit_12_Spectroscopy_Pulsed_Node(BaseNode):
    measurement_obj = Two_Tones_Multidim
    analysis_obj = QubitSpectroscopyAnalysis

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.sweep_range = self.node_dictionary.pop("sweep_range", None)
        self.redis_field = ['clock_freqs:f12']
        self.qubit_state = 1

        self.schedule_samplespace = {
            'spec_frequencies': {
                qubit: qubit_samples(qubit, '12', sweep_range=self.sweep_range) for qubit in self.all_qubits
            }
        }


class Qubit_12_Spectroscopy_Multidim_Node(BaseNode):
    measurement_obj = Two_Tones_Multidim
    analysis_obj = QubitSpectroscopyMultidim

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = [
            'clock_freqs:f12', 'spec:spec_ampl_12_optimal'
        ]
        self.qubit_state = 1

        self.schedule_samplespace = {
            'spec_pulse_amplitudes': {
                qubit: np.linspace(6e-3, 3e-2, 3) for qubit in self.all_qubits
            },
            'spec_frequencies': {
                qubit: qubit_samples(qubit, transition='12') for qubit in self.all_qubits
            },
        }


class Rabi_Oscillations_12_Node(BaseNode):
    measurement_obj = Rabi_Oscillations
    analysis_obj = RabiAnalysis

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['r12:ef_amp180']
        self.qubit_state = 1

        self.schedule_samplespace = {
            'mw_amplitudes': {
                qubit: np.linspace(0.002, 0.800, 61) for qubit in self.all_qubits
            }
        }
