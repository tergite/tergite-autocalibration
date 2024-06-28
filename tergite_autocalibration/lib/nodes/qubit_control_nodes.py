import numpy as np
from qblox_instruments.qcodes_drivers.cluster import Cluster

from tergite_autocalibration.lib.analysis.motzoi_analysis import MotzoiAnalysis
from tergite_autocalibration.lib.analysis.n_rabi_analysis import NRabiAnalysis
from tergite_autocalibration.lib.analysis.qubit_spectroscopy_analysis import (
    QubitSpectroscopyAnalysis,
)
from tergite_autocalibration.lib.analysis.qubit_spectroscopy_multidim import (
    QubitSpectroscopyMultidim,
)
from tergite_autocalibration.lib.analysis.rabi_analysis import RabiAnalysis
from tergite_autocalibration.lib.analysis.ramsey_analysis import RamseyAnalysis, RamseyDetuningsAnalysis
from tergite_autocalibration.lib.calibration_schedules.cw_two_nones_spectroscopy import CW_Two_Tones_Spectroscopy
from tergite_autocalibration.lib.calibration_schedules.motzoi_parameter import Motzoi_parameter
from tergite_autocalibration.lib.calibration_schedules.n_rabi_oscillations import (
    N_Rabi_Oscillations,
)
from tergite_autocalibration.lib.calibration_schedules.rabi_oscillations import Rabi_Oscillations
from tergite_autocalibration.lib.calibration_schedules.ramsey_detunings import Ramsey_detunings
from tergite_autocalibration.lib.calibration_schedules.ramsey_fringes import Ramsey_fringes
from tergite_autocalibration.lib.calibration_schedules.two_tone_multidim import Two_Tones_Multidim
from tergite_autocalibration.lib.calibration_schedules.two_tones_spectroscopy import Two_Tones_Spectroscopy
from tergite_autocalibration.lib.node_base import BaseNode
from tergite_autocalibration.lib.nodes.node_utils import qubit_samples
from tergite_autocalibration.utils.hardware_utils import set_qubit_LO


class Qubit_01_Spectroscopy_CW_Node(BaseNode):
    measurement_obj = CW_Two_Tones_Spectroscopy
    analysis_obj = QubitSpectroscopyMultidim

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.sweep_range = self.node_dictionary.pop("sweep_range", None)
        self.redis_field = ['clock_freqs:f01']

        self.operations_args = []

        self.external_samplespace = {
            'cw_frequencies': {
                qubit: qubit_samples(qubit) for qubit in self.all_qubits
            }
        }

    def pre_measurement_operation(self, reduced_ext_space):
        settable = list(reduced_ext_space.keys())[0]
        for instrument in self.lab_instr_coordinator.values():
            if type(instrument) == Cluster:
                cluster = instrument
        for qubit in self.all_qubits:
            lo_frequency = reduced_ext_space[settable][qubit]
            set_qubit_LO(cluster, qubit, lo_frequency)


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
                qubit: np.linspace(50e-4, 50e-4, 1) for qubit in self.all_qubits
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
                qubit: np.linspace(0.002, 0.90, 61) for qubit in self.all_qubits
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
                qubit: np.arange(-0.5, 0.5, 0.2) * 1e6 for qubit in self.all_qubits
            },
            # },
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
            }
        }



class Adaptive_Ramsey_Fringes_Node(BaseNode):
    measurement_obj = Ramsey_fringes
    analysis_obj = RamseyAnalysis

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['clock_freqs:f01']
        self.type = 'parameterized_sweep'
        self.backup = False
        self.post_process_each_iteration = True
        self.external_parameter_name = 'artificial_detuning'

        self.measurement_is_completed = False
        self.external_parameter_value = 0

        steps = [1,3,10,30,100]
        self.node_externals = 2.5 / (50 * np.array(steps) * 20e-9)
        self.external_iterations = len(self.node_externals)

    @property
    def samplespace(self):
        total_duration = 2.5 / self.external_parameter_value
        cluster_samplespace = {
            'ramsey_delays': {
                qubit: np.arange(20e-9, total_duration, 8 * 8e-9) for qubit in self.all_qubits
            },
        }
        return cluster_samplespace

    @property
    def dimensions(self):
        return (len(self.samplespace['ramsey_delays'][self.all_qubits[0]]), 1)




class Adaptive_Motzoi_Parameter_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        pass


    # measurement_obj = Motzoi_parameter
    # analysis_obj = AdaptiveMotzoiAnalysis
    # def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
    #     super().__init__(name, all_qubits, **node_dictionary)
    #     self.redis_field = ['rxy:motzoi']
    #     self.type = 'adaptive_sweep'
    #     self.adaptive_kwargs = defaultdict(dict)
    #     self.backup = False
    #     self.motzoi_minima = []
    #     # self.node_externals = np.arange(2, 52, 8)
    #     self.external_parameter_name = 'X_repetitions'
    #     self.external_parameter_value = 0
    #     self.measurement_is_completed = False
    #     self.node_samples = 41
    #     self.analysis_kwargs = {'samples': self.node_samples}
    #     repeats = [2,2+6,2+4*6,2+8*6,2+12*6,2+16*6]
    #     self.node_externals = np.array(repeats)
    #     self.samplespace = {
    #         'mw_motzois': {qubit: np.linspace(-0.4, 0.1, self.node_samples) for qubit in self.all_qubits},
    #     }
    # @property
    # def dimensions(self):
    #     return (len(self.samplespace['mw_motzois'][self.all_qubits[0]]), 1)



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
            }
        }


class N_Rabi_Oscillations_Node(BaseNode):
    measurement_obj = N_Rabi_Oscillations
    analysis_obj = NRabiAnalysis

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['rxy:amp180']
        self.backup = False

        self.schedule_samplespace = {
            'mw_amplitudes_sweep': {qubit: np.linspace(-0.03, 0.03, 51) for qubit in self.all_qubits},
            'X_repetitions': {qubit: np.arange(1, 21, 6) for qubit in self.all_qubits}
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
                qubit: np.linspace(50e-4, 50e-4, 1) for qubit in self.all_qubits
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
                qubit: np.linspace(0.002, 0.98, 41) for qubit in self.all_qubits
            }
        }
