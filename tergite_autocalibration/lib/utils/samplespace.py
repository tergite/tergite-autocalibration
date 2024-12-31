# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Michele Faucci Giannelli 2024
# (C) Copyright Stefan Hill 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np

from tergite_autocalibration.config.legacy import dh


def resonator_samples(qubit: str) -> np.ndarray:
    res_spec_samples = 91
    sweep_range = 4.0e6
    print(dh.get_legacy("VNA_resonator_frequencies")[qubit])
    VNA_frequency = dh.get_legacy("VNA_resonator_frequencies")[qubit]
    min_freq = VNA_frequency - sweep_range / 2
    max_freq = VNA_frequency + sweep_range / 2
    return np.linspace(min_freq, max_freq, res_spec_samples)


def qubit_samples(qubit: str, transition: str = "01") -> np.ndarray:
    qub_spec_samples = 91
    sweep_range = 10e6
    if transition == "01":
        VNA_frequency = dh.get_legacy("VNA_qubit_frequencies")[qubit]
    elif transition == "12":
        VNA_frequency = dh.get_legacy("VNA_f12_frequencies")[qubit]
    # FIXME: This is not safe, because VNA_frequency might be undefined
    min_freq = VNA_frequency - sweep_range / 2
    max_freq = VNA_frequency + sweep_range / 2
    return np.linspace(min_freq, max_freq, qub_spec_samples)
