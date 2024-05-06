from tergite_acl.config.VNA_LOKIB_values import (
    VNA_resonator_frequencies, VNA_qubit_frequencies, VNA_f12_frequencies
)
import numpy as np

def resonator_samples(qubit: str) -> np.ndarray:
    res_spec_samples = 81
    sweep_range = 4.0e6
    VNA_frequency = VNA_resonator_frequencies[qubit]
    min_freq = VNA_frequency - sweep_range / 2
    max_freq = VNA_frequency + sweep_range / 2
    return np.linspace(min_freq, max_freq, res_spec_samples)


def qubit_samples(qubit: str, transition: str = '01') -> np.ndarray:
    qub_spec_samples = 81
    sweep_range = 40e6
    if transition == '01':
        VNA_frequency = VNA_qubit_frequencies[qubit]
    elif transition == '12':
        VNA_frequency = VNA_f12_frequencies[qubit]
    else:
        VNA_frequency = VNA_value  # TODO: this should have a value
    min_freq = VNA_frequency - sweep_range / 2
    max_freq = VNA_frequency + sweep_range / 2
    return np.linspace(min_freq, max_freq, qub_spec_samples)