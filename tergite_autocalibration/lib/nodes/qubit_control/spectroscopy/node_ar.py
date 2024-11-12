# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Liangyu Chen 2023, 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np

# import xarray
# from tergite_autocalibration.config.VNA_values import (
#     VNA_qubit_frequencies,
#     VNA_f12_frequencies,
# )
# from lmfit.models import LorentzianModel
from tergite_autocalibration.lib.nodes.qubit_control.spectroscopy.analysis import (
    QubitSpectroscopyNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.qubit_control.spectroscopy.measurement_ar import (
    Two_Tones_Multidim_AR,
)

# TODO: check input
from tergite_autocalibration.utils.user_input import qubit_samples
from tergite_autocalibration.lib.base.schedule_node import ScheduleNode


class Qubit_01_Spectroscopy_Multidim_AR_Node(ScheduleNode):
    measurement_obj = Two_Tones_Multidim_AR
    analysis_obj = QubitSpectroscopyNodeAnalysis
    qubit_qois = ["clock_freqs:f01", "spec:spec_ampl_optimal"]

    def __init__(self, name: str, all_qubits: list[str], **schedule_kwargs):
        super().__init__(name, all_qubits, **schedule_kwargs)

        self.schedule_samplespace = {
            "spec_pulse_amplitudes": {
                qubit: np.linspace(4e-4, 8e-3, 2) for qubit in self.all_qubits
            },
            "spec_frequencies": {
                qubit: qubit_samples(qubit) for qubit in self.all_qubits
            },
        }
