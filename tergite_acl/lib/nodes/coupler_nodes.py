import numpy as np

from tergite_acl.config.settings import REDIS_CONNECTION
from tergite_acl.lib.analysis.coupler_spectroscopy_analysis import CouplerSpectroscopyAnalysis
from tergite_acl.lib.analysis.cz_calibration_analysis import CZCalibrationAnalysis, CZCalibrationSSROAnalysis
from tergite_acl.lib.analysis.cz_chevron_analysis import CZChevronAnalysis, CZChevronAnalysisReset
from tergite_acl.lib.analysis.reset_calibration_analysis import ResetCalibrationSSROAnalysis
from tergite_acl.lib.calibration_schedules.cz_calibration import CZ_calibration, CZ_calibration_SSRO
from tergite_acl.lib.calibration_schedules.cz_chevron_reversed import Reset_chevron_dc
from tergite_acl.lib.calibration_schedules.reset_calibration import Reset_calibration_SSRO
from tergite_acl.lib.node_base import BaseNode
from tergite_acl.lib.nodes.node_utils import qubit_samples, resonator_samples
from tergite_acl.lib.calibration_schedules.cz_chevron_reversed import CZ_chevron
from tergite_acl.lib.calibration_schedules.resonator_spectroscopy import Resonator_Spectroscopy
from tergite_acl.lib.calibration_schedules.two_tones_spectroscopy import Two_Tones_Spectroscopy
from tergite_acl.utils.hardware_utils import SpiRack
from tergite_acl.utils.hardware_utils import SpiDAC
from tergite_acl.config.coupler_config import coupler_spi_map
from tergite_acl.lib.calibration_schedules.randomized_benchmarking import Randomized_Benchmarking, TQG_Randomized_Benchmarking
from tergite_acl.lib.analysis.randomized_benchmarking_analysis import RandomizedBenchmarkingAnalysis



class Coupler_Spectroscopy_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], **node_dictionary):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = node_dictionary['couplers']
        self.redis_field = ['parking_current']
        self.qubit_state = 0
        self.type = 'spi_and_cluster_simple_sweep'
        # perform 2 tones while biasing the current
        self.measurement_obj = Two_Tones_Spectroscopy
        self.analysis_obj = CouplerSpectroscopyAnalysis
        self.coupled_qubits = self.get_coupled_qubits()
        self.sweep_range = self.node_dictionary.pop("sweep_range", None)
        self.external_parameter_name = 'currents'

        # self.validate()
        self.node_externals = np.round(np.append(np.arange(0.1, 3.1, 0.1),np.arange(-3, 0.1, 0.1)),1)*1e-3
        #self.node_externals = np.round(np.append([-0.1, -0.2] ,[0.1, 0]),1)*1e-3

        self.operations_args = []
        self.measure_qubit_index = 1
        self.measurement_qubit = self.coupled_qubits[self.measure_qubit_index]

        try:
            self.spi = SpiDAC()
        except:
            pass
        couplers = list(coupler_spi_map.keys())
        dacs = [self.spi.create_spi_dac(coupler) for coupler in couplers]
        self.coupler_dac = dict(zip(couplers,dacs))
        self.coupler = self.couplers[0] # we will generalize for multiple couplers later
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

    def pre_measurement_operation(self, external: float = 0): #external is the current
        print(f'Current: {external} for coupler: {self.coupler}')
        self.spi.set_dac_current(self.dac, external)
        
    @property
    def samplespace(self):
        cluster_samplespace = {
            'spec_frequencies': {self.measurement_qubit: qubit_samples(self.measurement_qubit)}
        }
        return cluster_samplespace


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

    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary):
        super().__init__(name, all_qubits,**node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
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
        q1_f01 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[0]}', "clock_freqs:f01"))
        q2_f01 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[1]}', "clock_freqs:f01"))
        q1_f12 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[0]}', "clock_freqs:f12"))
        q2_f12 = float(REDIS_CONNECTION.hget(f'transmons:{coupled_qubits[1]}', "clock_freqs:f12"))
        # ac_freq = np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12))
        ac_freq = np.min([np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12)),np.abs(q1_f01 + q2_f01 - (q2_f01 + q2_f12))])
        ac_freq = int(ac_freq / 1e4) * 1e4
        # lo = 4.4e9 - (ac_freq - 450e6) 
        # print(f'{ ac_freq/1e6 = } MHz for coupler: {coupler}')
        # print(f'{ lo/1e9 = } GHz for coupler: {coupler}')
        return ac_freq

    @property
    def samplespace(self):
        # print(f'{ np.linspace(- 50e6, 50e6, 2) + self.ac_freq = }')
        cluster_samplespace = {
            # For biase point sweep
            # 'cz_pulse_durations': {
            #     coupler: np.arange(0e-9, 401e-9, 20e-9)+40e-9 for coupler in self.couplers
            # },
            # 'cz_pulse_frequencies': {
            #     coupler: np.linspace(-12e6, 12e6, 21) + self.transition_frequency(coupler) for coupler in
            #     self.couplers
            # },
            # For CZ gate calibration
            'cz_pulse_durations': {
                coupler: np.arange(0e-9, 401e-9, 24e-9)+20e-9 for coupler in self.couplers
            },
            'cz_pulse_frequencies': {
                coupler: np.linspace(-10e6, 2e6, 25) + self.transition_frequency(coupler) for coupler in
                self.couplers
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
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.coupled_qubits = couplers[0].split(sep='_')
        self.redis_field = ['cz_phase', 'cz_pop_loss']
        self.qubit_state = 2
        self.testing_group = 0  # The edge group to be tested. 0 means all edges.
        self.measurement_obj = CZ_calibration
        self.analysis_obj = CZCalibrationAnalysis
        self.node_dictionary['dynamic'] = False
        self.node_dictionary['swap_type'] = False
        self.node_dictionary['use_edge'] = False
        # self.validate()

    @property
    def samplespace(self):
        cluster_samplespace = {
            'ramsey_phases': {qubit: np.append(np.linspace(0, 720, 51),[0,1]) for qubit in self.coupled_qubits},
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
        self.measurement_obj = CZ_calibration
        self.analysis_obj = CZCalibrationAnalysis
        self.node_dictionary['dynamic'] = True
        self.node_dictionary['swap_type'] = False
        self.node_dictionary['use_edge'] = False
    
    @property
    def samplespace(self):
        cluster_samplespace = {
            'ramsey_phases': {qubit: np.append(np.linspace(0, 720, 51),[0,1]) for qubit in self.coupled_qubits},
            'control_ons': {qubit: [False, True] for qubit in self.coupled_qubits},
        }
        return cluster_samplespace

class CZ_Dynamic_Phase_Swap_Node(BaseNode):
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
        self.measurement_obj = CZ_calibration
        self.analysis_obj = CZCalibrationAnalysis
        self.node_dictionary['dynamic'] = True
        self.node_dictionary['swap_type'] = True
        self.node_dictionary['use_edge'] = False

    
    @property
    def samplespace(self):
        cluster_samplespace = {
            'ramsey_phases': {qubit: np.append(np.linspace(0, 720, 51),[0,1]) for qubit in self.coupled_qubits},
            'control_ons': {qubit: [False, True] for qubit in self.coupled_qubits},
        }
        return cluster_samplespace

class TQG_Randomized_Benchmarking_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary):
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
        self.measurement_obj = TQG_Randomized_Benchmarking
        self.analysis_obj = RandomizedBenchmarkingAnalysis

        # TODO change it a dictionary like samplespace
        self.node_externals = 42 * np.arange(10, dtype=np.int32)
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
                qubit: np.array([1, 2, 3, 4, 8, 16, 32, 64, 128, 0, 1]) for qubit in self.all_qubits
                # qubit: np.array([1, 2,3,4,0, 1]) for qubit in self.all_qubits

            },
        }
        return cluster_samplespace

class TQG_Randomized_Benchmarking_Interleaved_Node(BaseNode):
    def __init__(self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary):
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
        self.measurement_obj = TQG_Randomized_Benchmarking
        self.analysis_obj = RandomizedBenchmarkingAnalysis
        self.node_dictionary['interleaving_clifford_id'] = 4386
        # TODO change it a dictionary like samplespace
        self.node_externals = 42 * np.arange(5, dtype=np.int32)
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
                # qubit: np.array([1, 2, 3, 4, 8, 16, 32, 64, 128, 0, 1]) for qubit in self.all_qubits
                qubit: np.array([1, 0, 1]) for qubit in self.all_qubits

            },
        }
        return cluster_samplespace