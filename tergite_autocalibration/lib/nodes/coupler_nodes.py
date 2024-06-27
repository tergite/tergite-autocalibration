import numpy as np

from tergite_autocalibration.lib.analysis.cz_firstStep_analysis import CZFirtStepAnalysis
from tergite_autocalibration.lib.calibration_schedules.cz_chevron_reversed import CZ_chevron
from tergite_autocalibration.lib.calibration_schedules.reset_calibration import Reset_calibration_SSRO

from tergite_autocalibration.config.coupler_config import coupler_spi_map
from tergite_autocalibration.config.settings import REDIS_CONNECTION
from tergite_autocalibration.lib.analysis.coupler_spectroscopy_analysis import CouplerSpectroscopyAnalysis
from tergite_autocalibration.lib.analysis.cz_calibration_analysis import CZCalibrationAnalysis, \
    CZCalibrationSSROAnalysis
from tergite_autocalibration.lib.analysis.cz_chevron_analysis import CZChevronAnalysis
from tergite_autocalibration.lib.analysis.cz_chevron_analysis import CZChevronAnalysisReset, \
    CZChevronAmplitudeAnalysis
from tergite_autocalibration.lib.analysis.randomized_benchmarking_analysis import RandomizedBenchmarkingAnalysis
from tergite_autocalibration.lib.analysis.reset_calibration_analysis import ResetCalibrationSSROAnalysis
from tergite_autocalibration.lib.calibration_schedules.cz_calibration import CZ_calibration, CZ_calibration_SSRO
from tergite_autocalibration.lib.calibration_schedules.cz_chevron_reversed import CZ_chevron_amplitude
from tergite_autocalibration.lib.calibration_schedules.randomized_benchmarking import TQG_Randomized_Benchmarking
from tergite_autocalibration.lib.calibration_schedules.reset_calibration import Reset_calibration_SSRO
from tergite_autocalibration.lib.calibration_schedules.resonator_spectroscopy import Resonator_Spectroscopy
from tergite_autocalibration.lib.calibration_schedules.two_tone_multidim import Two_Tones_Multidim
from tergite_autocalibration.lib.node_base import BaseNode
from tergite_autocalibration.lib.nodes.node_utils import qubit_samples, resonator_samples
from tergite_autocalibration.utils.hardware_utils import SpiDAC

RB_REPEATS = 10


class Coupler_Spectroscopy_Node(BaseNode):
    measurement_obj = Two_Tones_Multidim
    analysis_obj = CouplerSpectroscopyAnalysis

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = node_dictionary['couplers']
        self.redis_field = ['parking_current']
        self.qubit_state = 0
        self.type = 'spi_and_cluster_simple_sweep'
        # perform 2 tones while biasing the current
        self.coupled_qubits = self.get_coupled_qubits()
        self.sweep_range = self.node_dictionary.pop("sweep_range", None)
        self.external_parameter_name = 'currents'

        self.schedule_samplespace = {
            'spec_frequencies': {self.measurement_qubit: qubit_samples(self.measurement_qubit)}

        }

        self.external_samplespace = {
            'dc_currents': {
                self.coupler: np.arange(-2.5e-3, 2.5e-3, 250e-6)
            },
        }
        # self.validate()
        self.node_externals = np.round(np.append(np.arange(0.1, 3.1, 0.1), np.arange(-3, 0.1, 0.1)), 1) * 1e-3
        # self.node_externals = np.round(np.append([-0.1, -0.2] ,[0.1, 0]),1)*1e-3

        self.operations_args = []
        self.measure_qubit_index = 1
        self.measurement_qubit = self.coupled_qubits[self.measure_qubit_index]

        try:
            self.spi = SpiDAC()
        except:
            pass
        couplers = list(coupler_spi_map.keys())
        dacs = [self.spi.create_spi_dac(coupler) for coupler in couplers]
        self.coupler_dac = dict(zip(couplers, dacs))
        self.coupler = self.couplers[0]  # we will generalize for multiple couplers later
        self.dac = self.coupler_dac[self.coupler]

    def get_coupled_qubits(self) -> list:
        if len(self.couplers) > 1:
            print('Multiple couplers, lets work with only one')
        coupled_qubits = self.couplers[0].split(sep='_')
        self.coupler = self.couplers[0]
        return coupled_qubits

    @property
    def dimensions(self):
        return (len(self.samplespace['spec_frequencies'][self.measurement_qubit]), 1)

    def pre_measurement_operation(self, external: float = 0):  # external is the current
        print(f'Current: {external} for coupler: {self.coupler}')
        self.spi.set_dac_current(self.dac, external)

    @property
    def samplespace(self):
        cluster_samplespace = {
            'spec_frequencies': {self.measurement_qubit: qubit_samples(self.measurement_qubit)}
        }
        return cluster_samplespace


class Coupler_Resonator_Spectroscopy_Node(BaseNode):
    measurement_obj = Resonator_Spectroscopy
    analysis_obj = CouplerSpectroscopyAnalysis

    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        # TODO: Check on this node again the samplespace
        super().__init__(name, all_qubits, **node_dictionary)
        self.redis_field = ['resonator_flux_quantum']
        self.qubit_state = 0

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
    measurement_obj = CZ_chevron
    analysis_obj = CZChevronAnalysis

    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.redis_field = ['cz_pulse_frequency', 'cz_pulse_duration']
        self.qubit_state = 0
        self.all_qubits = [q for bus in couplers for q in bus.split('_')]
        self.coupler_samplespace = self.samplespace
        try:
            print(f'{self.node_dictionary["cz_pulse_amplitude"] = }')
        except:
            amplitude = float(REDIS_CONNECTION.hget(f'couplers:{self.coupler}', "cz_pulse_amplitude"))
            print(f'Amplitude found for coupler {self.coupler} : {amplitude}')
            if np.isnan(amplitude):
                amplitude = 0.375
                print(f'No amplitude found for coupler {self.coupler}. Using default value: {amplitude}')
            self.node_dictionary['cz_pulse_amplitude'] = amplitude

        self.schedule_samplespace = {
            'cz_pulse_durations': {
                coupler: np.arange(0e-9, 401e-9, 20e-9) + 100e-9 for coupler in self.couplers
            },
            'cz_pulse_frequencies': {
                coupler: np.linspace(-15e6, 10e6, 26) + self.transition_frequency(coupler) for coupler in
                self.couplers
            }
        }

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
        q1_f01 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[0]}', "clock_freqs:f01"))
        q2_f01 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[1]}', "clock_freqs:f01"))
        q1_f12 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[0]}', "clock_freqs:f12"))
        q2_f12 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[1]}', "clock_freqs:f12"))
        # ac_freq = np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12))
        ac_freq = np.max([np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12)), np.abs(q1_f01 + q2_f01 - (q2_f01 + q2_f12))])
        ac_freq = int(ac_freq / 1e4) * 1e4
        # lo = 4.4e9 - (ac_freq - 450e6)
        # print(f'{ ac_freq/1e6 = } MHz for coupler: {coupler}')
        # print(f'{ lo/1e9 = } GHz for coupler: {coupler}')
        return ac_freq

class CZ_Characterisation_Chevron_Node(BaseNode):
    measurement_obj = CZ_chevron
    analysis_obj = CZFirtStepAnalysis

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
        self.schedule_samplespace = {
            # For Wide sweep
            'cz_parking_current': {
                qubit: np.linspace(0.0008625, 0.0011625, 12) for qubit in self.coupled_qubits
            },
            'cz_pulse_amplitude': {
                qubit: np.linspace(0, 0.2, 3) for qubit in self.coupled_qubits
            },
            'cz_pulse_durations': {
                qubit: 80e-9+np.arange(0e-9, 400e-9,20e-9) for qubit in self.coupled_qubits
            },
            'cz_pulse_frequencies_sweep': {
                qubit: np.linspace(-20e6, 20e6, 21) + self.ac_freq for qubit in self.coupled_qubits
            },
        }
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
        ac_freq = np.min([np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12)),np.abs(q1_f01 + q2_f01 - (q2_f01 + q2_f12))])
        ac_freq = int(ac_freq / 1e4) * 1e4
        print(f'{ ac_freq/1e6 = } MHz for coupler: {coupler}')
        return ac_freq



class CZ_Chevron_Amplitude_Node(BaseNode):
    measurement_obj = CZ_chevron_amplitude
    analysis_obj = CZChevronAmplitudeAnalysis

    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.redis_field = ['cz_pulse_frequency', 'cz_pulse_amplitude']
        self.qubit_state = 0
        self.all_qubits = [q for bus in couplers for q in bus.split('_')]
        self.coupler_samplespace = self.samplespace
        self.node_dictionary["cz_pulse_duration"] = 128e-9
        REDIS_CONNECTION.hset(f"couplers:{self.coupler}", 'cz_pulse_duration',
                              self.node_dictionary["cz_pulse_duration"] * 2)
        self.schedule_samplespace = {
            'cz_pulse_amplitudes': {
                coupler: np.linspace(0.05, 0.3, 15) for coupler in self.couplers
            },
            'cz_pulse_frequencies': {
                coupler: np.linspace(-10e6, 6e6, 15) + self.transition_frequency(coupler) for coupler in
                self.couplers
            }
        }
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
        q1_f01 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[0]}', "clock_freqs:f01"))
        q2_f01 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[1]}', "clock_freqs:f01"))
        q1_f12 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[0]}', "clock_freqs:f12"))
        q2_f12 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[1]}', "clock_freqs:f12"))
        # ac_freq = np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12))
        ac_freq = np.max([np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12)), np.abs(q1_f01 + q2_f01 - (q2_f01 + q2_f12))])
        ac_freq = int(ac_freq / 1e4) * 1e4
        # lo = 4.4e9 - (ac_freq - 450e6)
        # print(f'{ ac_freq/1e6 = } MHz for coupler: {coupler}')
        # print(f'{ lo/1e9 = } GHz for coupler: {coupler}')
        return ac_freq


class CZ_Optimize_Chevron_Node(BaseNode):
    measurement_obj = CZ_chevron
    analysis_obj = CZChevronAnalysis

    def __init__(self, name: str, all_qubits: list[str], couplers: list[str]):
        super().__init__(name, all_qubits)
        self.type = 'optimized_sweep'
        self.couplers = couplers
        self.coupler = self.couplers[0]
        self.redis_field = ['cz_pulse_frequency', 'cz_pulse_duration']
        self.optimization_field = 'cz_pulse_duration'
        self.qubit_state = 0
        self.all_qubits = [q for bus in couplers for q in bus.split('_')]
        self.schedule_samplespace = {
            'cz_pulse_durations': {
                coupler: np.arange(100e-9, 1000e-9, 320e-9) for coupler in self.couplers
            },
            'cz_pulse_frequencies': {
                coupler: np.linspace(-2.0e6, 2.0e6, 5) + self.transition_frequency(coupler) for coupler in self.couplers
            }
        }
        self.coupler_samplespace = self.schedule_samplespace
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
        ac_freq = np.max([np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12)), np.abs(q1_f01 + q2_f01 - (q2_f01 + q2_f12))])
        ac_freq = int(ac_freq / 1e4) * 1e4
        print(f'{ ac_freq/1e6 = } MHz for coupler: {coupler}')
        return ac_freq


class Reset_Chevron_Node(BaseNode):
    #TODO: Replaced Reset_CZ_Chevron with Reset_calibration_SSRO, is that correct?
    measurement_obj = Reset_calibration_SSRO
    analysis_obj = CZChevronAnalysisReset

    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.redis_field = ['reset_amplitude_qc', 'reset_duration_qc']
        self.qubit_state = 0
        self.coupled_qubits = self.couplers[0].split(sep='_')
        self.schedule_samplespace = {
            'cz_pulse_durations': {  # g
                qubit: np.linspace(0.001, 0.1, 26) for qubit in self.coupled_qubits
            },
            'cz_pulse_amplitudes': {  # ft
                qubit: np.linspace(0, -0.4, 26) for qubit in self.coupled_qubits
            },
        }
        # self.node_dictionary['duration_offset'] = 0
        # print(f'{ self.coupled_qubits = }')


class CZ_Calibration_Node(BaseNode):
    measurement_obj = CZ_calibration
    analysis_obj = CZCalibrationAnalysis

    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.coupled_qubits = couplers[0].split(sep='_')
        self.redis_field = ['cz_phase', 'cz_pop_loss']
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.
        self.node_dictionary['dynamic'] = False
        self.node_dictionary['swap_type'] = False
        self.schedule_samplespace = {
            'ramsey_phases': {qubit: np.append(np.linspace(0, 360, 25), [0, 1]) for qubit in self.coupled_qubits},
            'control_ons': {qubit: [False, True] for qubit in self.coupled_qubits},
        }
        # self.node_dictionary['use_edge'] = False
        # self.node_dictionary['number_of_cz'] = 1
        # self.validate()


class CZ_Calibration_SSRO_Node(BaseNode):
    measurement_obj = CZ_calibration_SSRO
    analysis_obj = CZCalibrationSSROAnalysis

    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.coupler = couplers[0]
        self.coupled_qubits = couplers[0].split(sep='_')
        # self.node_dictionary = kwargs
        self.edges = couplers
        self.redis_field = ['cz_phase', 'cz_pop_loss', 'cz_leakage']
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.
        self.node_dictionary['dynamic'] = False
        self.node_dictionary['swap_type'] = False
        self.schedule_samplespace = {
            'control_ons': {qubit: [False, True] for qubit in self.coupled_qubits},
            'ramsey_phases': {qubit: np.linspace(0, 360, 25) for qubit in self.coupled_qubits},
            # 'ramsey_phases': {qubit: np.linspace(0.025, 0.025, 1) for qubit in  self.coupled_qubits},
        }
        # self.validate()


class CZ_Calibration_Swap_Node(BaseNode):
    measurement_obj = CZ_calibration
    analysis_obj = CZCalibrationAnalysis

    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.coupled_qubits = couplers[0].split(sep='_')
        self.redis_field = ['cz_phase', 'cz_pop_loss']
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.

        self.node_dictionary['dynamic'] = False
        self.node_dictionary['swap_type'] = True
        self.schedule_samplespace = {
            'ramsey_phases': {qubit: np.append(np.linspace(0, 360, 25), [0, 1]) for qubit in self.coupled_qubits},
            'control_ons': {qubit: [False, True] for qubit in self.coupled_qubits},
        }
        # self.node_dictionary['use_edge'] = False
        # self.node_dictionary['number_of_cz'] = 1
        # self.validate()


class CZ_Calibration_Swap_SSRO_Node(BaseNode):
    measurement_obj = CZ_calibration_SSRO
    analysis_obj = CZCalibrationSSROAnalysis

    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.coupler = couplers[0]
        self.coupled_qubits = couplers[0].split(sep='_')
        # self.node_dictionary = kwargs
        self.edges = couplers
        self.redis_field = ['cz_phase', 'cz_pop_loss', 'cz_leakage']
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.
        self.node_dictionary['dynamic'] = False
        self.node_dictionary['swap_type'] = True
        self.schedule_samplespace = {
            'control_ons': {qubit: [False, True] for qubit in self.coupled_qubits},
            'ramsey_phases': {qubit: np.linspace(0, 360, 25) for qubit in self.coupled_qubits},
            # 'ramsey_phases': {qubit: np.linspace(0.025, 0.025, 1) for qubit in  self.coupled_qubits},
        }
        # self.validate()


class Reset_Calibration_SSRO_Node(BaseNode):
    measurement_obj = Reset_calibration_SSRO
    analysis_obj = ResetCalibrationSSROAnalysis

    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = couplers[0]
        # print(couplers)
        self.coupled_qubits = couplers[0].split(sep='_')
        # print(self.coupled_qubits)
        # self.node_dictionary = kwargs
        self.redis_field = ['reset_fidelity', 'reset_leakage', 'all_fidelity', 'all_fidelity_f']
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.
        self.dynamic = False
        self.node_dictionary['swap_type'] = True
        self.schedule_samplespace = {
            'control_ons': {qubit: [False, True] for qubit in self.coupled_qubits},
            'ramsey_phases': {qubit: range(9) for qubit in self.coupled_qubits},
        }
        # self.validate()


class CZ_Dynamic_Phase_Node(BaseNode):
    measurement_obj = CZ_calibration
    analysis_obj = CZCalibrationAnalysis

    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.coupled_qubits = couplers[0].split(sep='_')
        self.redis_field = ['cz_dynamic_target']
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.
        self.node_dictionary['dynamic'] = True
        self.node_dictionary['swap_type'] = False
        self.node_dictionary['use_edge'] = False
        self.schedule_samplespace = {
            'ramsey_phases': {qubit: np.append(np.linspace(0, 360, 25), [0, 1]) for qubit in self.coupled_qubits},
            'control_ons': {qubit: [False, True] for qubit in self.coupled_qubits},
        }


class CZ_Dynamic_Phase_Swap_Node(BaseNode):
    measurement_obj = CZ_calibration
    analysis_obj = CZCalibrationAnalysis

    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.coupled_qubits = couplers[0].split(sep='_')
        self.redis_field = ['cz_dynamic_control']
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.
        self.node_dictionary['dynamic'] = True
        self.node_dictionary['swap_type'] = True
        self.node_dictionary['use_edge'] = False
        self.schedule_samplespace = {
            'ramsey_phases': {qubit: np.append(np.linspace(0, 360, 25), [0, 1]) for qubit in self.coupled_qubits},
            'control_ons': {qubit: [False, True] for qubit in self.coupled_qubits},
        }


class TQG_Randomized_Benchmarking_Node(BaseNode):
    measurement_obj = TQG_Randomized_Benchmarking
    analysis_obj = RandomizedBenchmarkingAnalysis

    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary):
        # TODO: Check this node whether the logic is working
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.type = 'parameterized_sweep'
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.coupled_qubits = couplers[0].split(sep='_')
        self.node_dictionary = node_dictionary
        self.backup = False
        self.redis_field = ['tqg_fidelity']

        self.schedule_samplespace = {
            'number_of_cliffords': {
                # qubit: all_numbers for qubit in self.all_qubits
                qubit: np.array([0, 2, 4, 8, 16, 32, 64, 128, 0, 1, 2]) for qubit in self.all_qubits
                # qubit: np.array([1, 2,3,4,0, 1]) for qubit in self.all_qubits

            },
        }

        # TODO change it a dictionary like samplespace
        self.node_externals = 42 * np.arange(RB_REPEATS, dtype=np.int32)
        self.external_parameter_name = 'seed'
        self.external_parameter_value = 0
        ####################

    @property
    def dimensions(self):
        return (len(self.samplespace['number_of_cliffords'][self.all_qubits[0]]), 1)

    @property
    def samplespace(self):
        numbers = 2 ** np.arange(1, 12, 3)
        extra_numbers = [numbers[i] + numbers[i + 1] for i in range(len(numbers) - 2)]
        extra_numbers = np.array(extra_numbers)
        calibration_points = np.array([0, 1])
        all_numbers = np.sort(np.concatenate((numbers, extra_numbers)))
        # all_numbers = numbers

        all_numbers = np.concatenate((all_numbers, calibration_points))

        # number_of_repetitions = 1

        cluster_samplespace = {
            'number_of_cliffords': {
                # qubit: all_numbers for qubit in self.all_qubits
                qubit: np.array([0, 2, 4, 8, 16, 32, 64, 128, 0, 1, 2]) for qubit in self.all_qubits
                # qubit: np.array([1, 2,3,4,0, 1]) for qubit in self.all_qubits

            },
        }
        return cluster_samplespace


class TQG_Randomized_Benchmarking_Interleaved_Node(BaseNode):
    measurement_obj = TQG_Randomized_Benchmarking
    analysis_obj = RandomizedBenchmarkingAnalysis

    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary):
        # TODO: Check here as well the samplespace and whether it is working as expected
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.type = 'parameterized_sweep'
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.coupled_qubits = couplers[0].split(sep='_')
        self.node_dictionary = node_dictionary
        self.backup = False
        self.redis_field = ['tqg_fidelity_interleaved']
        self.schedule_samplespace = {
            'number_of_cliffords': {
                # qubit: all_numbers for qubit in self.all_qubits
                qubit: np.array([0, 1, 2, 3, 4, 8, 16, 32, 64, 128, 0, 1]) for qubit in self.all_qubits
                # qubit: np.array([1, 0, 1]) for qubit in self.all_qubits

            },
        }

        self.node_dictionary['interleaving_clifford_id'] = 4386
        # TODO change it a dictionary like samplespace
        self.node_externals = 42 * np.arange(RB_REPEATS, dtype=np.int32)
        self.external_parameter_name = 'seed'
        self.external_parameter_value = 0
        ####################

    @property
    def dimensions(self):
        return (len(self.samplespace['number_of_cliffords'][self.all_qubits[0]]), 1)

    @property
    def samplespace(self):
        numbers = 2 ** np.arange(1, 12, 3)
        extra_numbers = [numbers[i] + numbers[i + 1] for i in range(len(numbers) - 2)]
        extra_numbers = np.array(extra_numbers)
        calibration_points = np.array([0, 1])
        all_numbers = np.sort(np.concatenate((numbers, extra_numbers)))
        # all_numbers = numbers

        all_numbers = np.concatenate((all_numbers, calibration_points))

        # number_of_repetitions = 1

        cluster_samplespace = {
            'number_of_cliffords': {
                # qubit: all_numbers for qubit in self.all_qubits
                qubit: np.array([0, 1, 2, 3, 4, 8, 16, 32, 64, 128, 0, 1]) for qubit in self.all_qubits
                # qubit: np.array([1, 0, 1]) for qubit in self.all_qubits

            },
        }
        return cluster_samplespace
