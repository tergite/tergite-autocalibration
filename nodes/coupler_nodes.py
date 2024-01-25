import numpy as np
from calibration_schedules.two_tones_spectroscopy import Two_Tones_Spectroscopy
from calibration_schedules.resonator_spectroscopy import Resonator_Spectroscopy
from analysis.coupler_spectroscopy_analysis import CouplerSpectroscopyAnalysis
from config_files.VNA_LOKIB_values import VNA_resonator_frequencies, VNA_qubit_frequencies, VNA_f12_frequencies
from nodes.node import Base_Node

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
        VNA_frequency = VNA_value
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
        # print(f'{ self.coupled_qubits = }')
        # print(f'{ qubit = }')
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

