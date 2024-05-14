import numpy as np

from tergite_acl.config.settings import REDIS_CONNECTION
from tergite_acl.lib.analysis.coupler_spectroscopy_analysis import CouplerSpectroscopyAnalysis
from tergite_acl.lib.analysis.cz_calibration_analysis import CZCalibrationAnalysis, CZCalibrationSSROAnalysis
from tergite_acl.lib.analysis.cz_chevron_analysis import CZChevronAnalysis, CZChevronAnalysisReset
from tergite_acl.lib.analysis.reset_calibration_analysis import ResetCalibrationSSROAnalysis
from tergite_acl.lib.analysis.cz_firstStep_analysis import CZFirtStepAnalysis 
from tergite_acl.lib.calibration_schedules.cz_calibration import CZ_calibration, CZ_calibration_SSRO, CZ_dynamic_phase
from tergite_acl.lib.calibration_schedules.cz_chevron_reversed import Reset_chevron_dc
from tergite_acl.lib.calibration_schedules.reset_calibration import Reset_calibration_SSRO
from tergite_acl.lib.node_base import BaseNode
from tergite_acl.lib.nodes.node_utils import qubit_samples, resonator_samples
from tergite_acl.lib.calibration_schedules.cz_chevron_reversed import CZ_chevron
from tergite_acl.lib.calibration_schedules.resonator_spectroscopy import Resonator_Spectroscopy
from tergite_acl.lib.calibration_schedules.two_tones_spectroscopy import Two_Tones_Spectroscopy


class Coupler_Spectroscopy_Node:
    def __init__(self, name: str, all_qubits: list[str], **kwargs):
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = kwargs['couplers']
        self.redis_field = ['parking_current']
        self.qubit_state = 0
        # perform 2 tones while biasing the current
        self.measurement_obj = Two_Tones_Spectroscopy
        self.analysis_obj = CouplerSpectroscopyAnalysis
        self.coupled_qubits = self.get_coupled_qubits()
        # self.validate()

    def get_coupled_qubits(self) -> list:
        if len(self.couplers) > 1:
            print('Multiple couplers, lets work with only one')
        coupled_qubits = self.couplers[0].split(sep='_')
        self.coupler = self.couplers[0]
        return coupled_qubits

    @property
    def samplespace(self):
        qubit = self.coupled_qubits[self.measure_qubit_index]
        self.measurement_qubit = qubit
        cluster_samplespace = {
            'spec_frequencies': {qubit: qubit_samples(qubit, sweep_range=self.sweep_range)}
        }
        # cluster_samplespace = {
        #     'spec_frequencies': {qubit: np.linspace(3.771, 3.971, 0.0005)}
        # }
        return cluster_samplespace

    @property
    def spi_samplespace(self):
        spi_samplespace = {
            'dc_currents': {self.couplers[0]: np.append(np.arange(0e-3, 3e-3, 100e-6),np.arange(0e-3, -3e-3, -100e-6))},
        }
        return spi_samplespace


class Coupler_Resonator_Spectroscopy_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['resonator_flux_quantum']
        self.qubit_state = 0
        self.measurement_obj = Resonator_Spectroscopy
        self.analysis_obj = CouplerSpectroscopyAnalysis

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


class CZ_Chevron_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], couplers: list[str]):
        super().__init__(name, all_qubits)
        self.couplers = couplers
        self.coupler = self.couplers[0]
        self.redis_field = ['cz_pulse_frequency', 'cz_pulse_duration']
        self.qubit_state = 0
        self.measurement_obj = CZ_chevron
        self.analysis_obj = CZChevronAnalysis
        self.all_qubits = [q for bus in couplers for q in bus.split('_')]
        self.coupler_samplespace = self.samplespace
        self.validate()

    def validate(self) -> None:
        all_coupled_qubits = []
        for coupler in self.couplers:
            all_coupled_qubits += coupler.split('_')
        if len(all_coupled_qubits) > len(set(all_coupled_qubits)):
            print('Couplers share qubits')
            raise ValueError('Improper Couplers')

    def transition_frequency(self, coupler: str):
        coupled_qubits = coupler.split(sep='_')
        q1_f01 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[0]}', "freq_01"))
        q2_f01 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[1]}', "freq_01"))
        q1_f12 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[0]}', "freq_12"))
        q2_f12 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[1]}', "freq_12"))
        # ac_freq = np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12))
        ac_freq = np.abs(q1_f01 + q2_f01 - (q2_f01 + q2_f12))
        ac_freq = int(ac_freq / 1e4) * 1e4
        print(f'{ ac_freq/1e6 = } MHz for coupler: {coupler}')
        return ac_freq

    @property
    def samplespace(self):
        # print(f'{ np.linspace(- 50e6, 50e6, 2) + self.ac_freq = }')
        cluster_samplespace = {
            # For Wide sweep
            # 'cz_pulse_durations': {
            #     qubit: 4e-9+np.arange(0e-9, 36*100e-9,400e-9) for qubit in self.coupled_qubits
            # },
            # 'cz_pulse_frequencies_sweep': {
            #     qubit: np.linspace(210e6, 500e6, 51) + self.ac_freq for qubit in self.coupled_qubits
            # },

            # For CZ gate
            'cz_pulse_durations': {
                coupler: np.arange(100e-9, 1000e-9, 32e-9) for coupler in self.couplers
            },
            'cz_pulse_frequencies': {
                coupler: np.linspace(-2.0e6, 2.0e6, 25) + self.transition_frequency(coupler) for coupler in
                self.couplers
            },
        }
        return cluster_samplespace


class CZ_Characterisation_Chevron_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], couplers: list[str]):
        super().__init__(name, all_qubits)
        self.type = 'characterisation_sweep'
        self.couplers = couplers
        self.coupler = self.couplers[0]
        self.redis_field = ['cz_parking_current', 'cz_pulse_amplitude', 'cz_pulse_frequency', 'cz_pulse_duration']
        self.optimization_field = 'cz_parking_current', 'cz_pulse_amplitude', 'cz_pulse_frequency', 'cz_pulse_duration'
        self.qubit_state = 0
        self.measurement_obj = CZ_chevron
        self.analysis_obj = CZFirtStepAnalysis
        self.all_qubits = [q for bus in couplers for q in bus.split('_')]
        self.coupler_samplespace = self.samplespace
        self.validate()

    def validate(self) -> None:
        all_coupled_qubits = []
        for coupler in self.couplers:
            all_coupled_qubits += coupler.split('_')
        if len(all_coupled_qubits) > len(set(all_coupled_qubits)):
            print('Couplers share qubits')
            raise ValueError('Improper Couplers')

    def transition_frequency(self, coupler: str):
        coupled_qubits = coupler.split(sep='_')
        q1_f01 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[0]}', "freq_01"))
        q2_f01 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[1]}', "freq_01"))
        q1_f12 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[0]}', "freq_12"))
        q2_f12 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[1]}', "freq_12"))
        # ac_freq = np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12))
        ac_freq = np.abs(q1_f01 + q2_f01 - (q2_f01 + q2_f12))
        ac_freq = int(ac_freq / 1e4) * 1e4
        print(f'{ ac_freq/1e6 = } MHz for coupler: {coupler}')
        return ac_freq

    @property
    def samplespace(self):
        # print(f'{ np.linspace(- 50e6, 50e6, 2) + self.ac_freq = }')
        cluster_samplespace = {
            # For Wide sweep
            'cz_parking_current': {
                qubit: np.linspace(0.0008625, 0.0011625, 12) for qubit in self.coupled_qubits
            },
            'cz_pulse_amplitude': {
                qubit: np.linspace(0, 0.2, 3) for qubit in self.coupled_qubits
            },
            'cz_pulse_durations': {
                qubit: 4e-9+np.arange(0e-9, 36*100e-9,400e-9) for qubit in self.coupled_qubits
            },
            'cz_pulse_frequencies_sweep': {
                qubit: np.linspace(210e6, 500e6, 51) + self.ac_freq for qubit in self.coupled_qubits
            },
        }
        return cluster_samplespace


class CZ_Optimize_Chevron_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], couplers: list[str]):
        super().__init__(name, all_qubits)
        self.type = 'optimized_sweep'
        self.couplers = couplers
        self.coupler = self.couplers[0]
        self.redis_field = ['cz_pulse_frequency', 'cz_pulse_duration']
        self.optimization_field = 'cz_pulse_duration'
        self.qubit_state = 0
        self.measurement_obj = CZ_chevron
        self.analysis_obj = CZChevronAnalysis
        self.all_qubits = [q for bus in couplers for q in bus.split('_')]
        self.coupler_samplespace = self.samplespace
        self.validate()

    def validate(self) -> None:
        all_coupled_qubits = []
        for coupler in self.couplers:
            all_coupled_qubits += coupler.split('_')
        if len(all_coupled_qubits) > len(set(all_coupled_qubits)):
            print('Couplers share qubits')
            raise ValueError('Improper Couplers')

    def transition_frequency(self, coupler: str):
        coupled_qubits = coupler.split(sep='_')
        q1_f01 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[0]}', "freq_01"))
        q2_f01 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[1]}', "freq_01"))
        q1_f12 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[0]}', "freq_12"))
        q2_f12 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[1]}', "freq_12"))
        # ac_freq = np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12))
        ac_freq = np.abs(q1_f01 + q2_f01 - (q2_f01 + q2_f12))
        ac_freq = int(ac_freq / 1e4) * 1e4
        print(f'{ ac_freq/1e6 = } MHz for coupler: {coupler}')
        return ac_freq

    @property
    def samplespace(self):
        # print(f'{ np.linspace(- 50e6, 50e6, 2) + self.ac_freq = }')
        cluster_samplespace = {
            # For Wide sweep
            # 'cz_pulse_durations': {
            #     qubit: 4e-9+np.arange(0e-9, 36*100e-9,400e-9) for qubit in self.coupled_qubits
            # },
            # 'cz_pulse_frequencies_sweep': {
            #     qubit: np.linspace(210e6, 500e6, 51) + self.ac_freq for qubit in self.coupled_qubits
            # },

            # For CZ gate
            'cz_pulse_durations': {
                coupler: np.arange(100e-9, 1000e-9, 320e-9) for coupler in self.couplers
            },
            'cz_pulse_frequencies': {
                coupler: np.linspace(-2.0e6, 2.0e6, 5) + self.transition_frequency(coupler) for coupler in self.couplers
            },
        }
        return cluster_samplespace

class Reset_Chevron_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.all_couplers = couplers
        self.coupler = couplers[0]
        self.redis_field = ['reset_amplitude_qc', 'reset_duration_qc']
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
                qubit: 4e-9 + np.linspace(16e-9, 16e-9, 11) for qubit in self.coupled_qubits
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


class CZ_Calibration_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.coupler = couplers[0]
        # print(couplers)
        self.coupled_qubits = couplers[0].split(sep='_')
        # print(self.coupled_qubits)
        # self.node_dictionary = kwargs
        self.redis_field = ['cz_phase', 'cz_pop_loss']
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.
        self.dynamic = False
        self.measurement_obj = CZ_calibration
        self.analysis_obj = CZCalibrationAnalysis
        # self.validate()

    @property
    def samplespace(self):
        cluster_samplespace = {
            'ramsey_phases': {qubit: np.linspace(0, 360, 31) for qubit in self.coupled_qubits},
            'control_ons': {qubit: [False, True] for qubit in self.coupled_qubits},
        }
        return cluster_samplespace


class CZ_Calibration_SSRO_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.coupler = couplers[0]
        self.coupled_qubits = couplers[0].split(sep='_')
        # self.node_dictionary = kwargs
        self.redis_field = ['cz_phase', 'cz_pop_loss', 'cz_leakage']
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.
        self.dynamic = False
        self.measurement_obj = CZ_calibration_SSRO
        self.analysis_obj = CZCalibrationSSROAnalysis
        # self.validate()

    @property
    def samplespace(self):
        cluster_samplespace = {
            'control_ons': {qubit: [False, True] for qubit in self.coupled_qubits},
            'ramsey_phases': {qubit: np.linspace(0, 360, 13) for qubit in self.coupled_qubits},
            # 'ramsey_phases': {qubit: np.linspace(0.025, 0.025, 1) for qubit in  self.coupled_qubits},
        }
        return cluster_samplespace

class Reset_Calibration_SSRO_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], ** node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.coupler = couplers[0]
        # print(couplers)
        self.coupled_qubits = couplers[0].split(sep='_')
        # print(self.coupled_qubits)
        # self.node_dictionary = kwargs
        self.redis_field = ['reset_fidelity','reset_leakage']
        self.qubit_state = 2
        self.testing_group = 0 # The edge group to be tested. 0 means all edges.
        self.dynamic = False
        self.measurement_obj = Reset_calibration_SSRO
        self.analysis_obj = ResetCalibrationSSROAnalysis
        # self.validate()

    @property
    def samplespace(self):
        cluster_samplespace = {
            'control_ons': {qubit: [False,True] for qubit in  self.coupled_qubits},
            'ramsey_phases': {qubit: range(9) for qubit in  self.coupled_qubits},
        }
        return cluster_samplespace




class CZ_Dynamic_Phase_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], **kwargs):
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
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.
        self.dynamic = True
        self.measurement_obj = CZ_dynamic_phase
        self.analysis_obj = CZCalibrationAnalysis
