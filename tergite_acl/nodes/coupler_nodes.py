import numpy as np
import redis
from tergite_acl.calibration_schedules.cz_chevron_reversed import CZ_chevron
from tergite_acl.calibration_schedules.two_tones_spectroscopy import Two_Tones_Spectroscopy
from tergite_acl.calibration_schedules.resonator_spectroscopy import Resonator_Spectroscopy
from tergite_acl.analysis.coupler_spectroscopy_analysis import CouplerSpectroscopyAnalysis
from tergite_acl.analysis.cz_chevron_analysis import CZChevronAnalysis
from tergite_acl.config_files.VNA_LOKIB_values import VNA_resonator_frequencies, VNA_qubit_frequencies, VNA_f12_frequencies
from tergite_acl.nodes.base_node import Base_Node

redis_connection = redis.Redis(decode_responses=True)

def resonator_samples(qubit: str) -> np.ndarray:
    res_spec_samples = 101
    sweep_range =  2.0e6
    VNA_frequency = VNA_resonator_frequencies[qubit]
    min_freq = VNA_frequency - sweep_range / 2 -0.5e6
    max_freq = VNA_frequency + sweep_range / 2
    return np.linspace(min_freq, max_freq, res_spec_samples)


def qubit_samples(qubit: str, transition: str = '01') -> np.ndarray:
    qub_spec_samples = 41
    sweep_range = 3.0e6
    if transition == '01':
        VNA_frequency = VNA_qubit_frequencies[qubit]
    elif transition == '12':
        VNA_frequency = VNA_f12_frequencies[qubit]
    else:
        VNA_frequency = VNA_value # TODO: this should have a value
    min_freq = VNA_frequency - sweep_range / 2
    max_freq = VNA_frequency + sweep_range / 2
    return np.linspace(min_freq, max_freq, qub_spec_samples)

class Coupler_Spectroscopy_Node:
    def __init__(self, name: str, all_qubits: list[str], ** kwargs):
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
            'dc_currents': {self.couplers[0]: np.arange(-2.5e-3, 2.5e-3, 250e-6)},
        }
        return spi_samplespace

class Coupler_Resonator_Spectroscopy_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], ** node_dictionary):
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


class CZ_Chevron_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], couplers: list[str]):
        super().__init__(name, all_qubits)
        self.couplers = couplers
        self.coupler = self.couplers[0]
        self.redis_field = ['cz_pulse_frequency','cz_pulse_duration']
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
        q1_f01 = float(redis_connection.hget(f'transmons:{coupled_qubits[0]}', "freq_01"))
        q2_f01 = float(redis_connection.hget(f'transmons:{coupled_qubits[1]}', "freq_01"))
        q1_f12 = float(redis_connection.hget(f'transmons:{coupled_qubits[0]}', "freq_12"))
        q2_f12 = float(redis_connection.hget(f'transmons:{coupled_qubits[1]}', "freq_12"))
        # ac_freq = np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12))
        ac_freq = np.abs(q1_f01 + q2_f01 - (q2_f01 + q2_f12))
        ac_freq = int( ac_freq / 1e4 ) * 1e4
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
                coupler: np.linspace(-2.0e6, 2.0e6, 25) + self.transition_frequency(coupler) for coupler in self.couplers
            },
        }
        return cluster_samplespace


class CZ_Optimize_Chevron_Node(Base_Node):
    def __init__(self, name: str, all_qubits: list[str], couplers: list[str]):
        super().__init__(name, all_qubits)
        self.type = 'optimized_sweep'
        self.couplers = couplers
        self.coupler = self.couplers[0]
        self.redis_field = ['cz_pulse_frequency','cz_pulse_duration']
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
        q1_f01 = float(redis_connection.hget(f'transmons:{coupled_qubits[0]}', "freq_01"))
        q2_f01 = float(redis_connection.hget(f'transmons:{coupled_qubits[1]}', "freq_01"))
        q1_f12 = float(redis_connection.hget(f'transmons:{coupled_qubits[0]}', "freq_12"))
        q2_f12 = float(redis_connection.hget(f'transmons:{coupled_qubits[1]}', "freq_12"))
        # ac_freq = np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12))
        ac_freq = np.abs(q1_f01 + q2_f01 - (q2_f01 + q2_f12))
        ac_freq = int( ac_freq / 1e4 ) * 1e4
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
