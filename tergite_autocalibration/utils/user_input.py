import numpy as np

VNA = {
    "VNA_resonator_frequencies": {"q01": 6000000000.0, "q02": 6100000000.0},
    "VNA_qubit_frequencies": {"q01": 6000000000.0, "q02": 6100000000.0},
    "VNA_f12_frequencies": {"q01": 6000000000.0, "q02": 6100000000.0},
}
VNA_resonator_frequencies = VNA["VNA_resonator_frequencies"]
VNA_qubit_frequencies = VNA["VNA_qubit_frequencies"]
VNA_f12_frequencies = VNA["VNA_f12_frequencies"]


def resonator_samples(qubit: str) -> np.ndarray:
    res_spec_samples = 70
    sweep_range = 5.0e6
    VNA_frequency = VNA_resonator_frequencies[qubit]
    min_freq = VNA_frequency - sweep_range / 2
    max_freq = VNA_frequency + sweep_range / 2
    return np.linspace(min_freq, max_freq, res_spec_samples)


def qubit_samples(qubit: str, transition: str = "01") -> np.ndarray:
    qub_spec_samples = 51
    sweep_range = 10e6
    if transition == "01":
        VNA_frequency = VNA_qubit_frequencies[qubit]
    elif transition == "12":
        VNA_frequency = VNA_f12_frequencies[qubit]
    min_freq = VNA_frequency - sweep_range / 2
    max_freq = VNA_frequency + sweep_range / 2
    return np.linspace(min_freq, max_freq, qub_spec_samples)
