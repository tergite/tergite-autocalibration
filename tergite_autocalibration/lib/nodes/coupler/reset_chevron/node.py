# This code is part of Tergite
#
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Amr Osman 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np

from tergite_autocalibration.lib.base.node import BaseNode
from tergite_autocalibration.lib.nodes.coupler.reset_chevron.analysis import (
    ResetChevronAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.reset_chevron.measurement import (
    Reset_Chevron_DC,
)


class Reset_Chevron_Node(BaseNode):
    measurement_obj = Reset_Chevron_DC
    analysis_obj = ResetChevronAnalysis

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.redis_field = ["reset_amplitude_qc", "reset_duration_qc"]
        self.qubit_state = 0
        self.all_qubits = [q for bus in couplers for q in bus.split("_")]
        self.coupler_samplespace = self.samplespace

        self.schedule_samplespace = {
            # Pulse test
            # 'reset_pulse_durations': {
            #     qubit: 4e-9 + np.linspace(16e-9, 16e-9, 21) for qubit in self.coupled_qubits
            # },
            # 'reset_pulse_amplitudes': {
            #     qubit: np.linspace(0.4, 0.4, 21) for qubit in self.coupled_qubits
            # },
            # For DC reset
            # q22_q23
            # 'reset_pulse_durations': {
            #     qubit: 0e-9+np.linspace(40, 80, 4)*1e-9 for qubit in self.coupled_qubits
            # },
            # 'reset_pulse_amplitudes': {
            #     qubit: np.linspace(-0.14, -0.15, 4) for qubit in self.coupled_qubits
            # },
            # q23_q24
            "reset_pulse_durations": {
                coupler: 1e-9 + np.linspace(0, 240, 41) * 1e-9
                for coupler in self.couplers
            },
            "reset_pulse_amplitudes": {
                coupler: np.linspace(-0.12, -0.26, 21) for coupler in self.couplers
            },
            # q24_q25
            # 'reset_pulse_durations': {
            #     coupler: 0e-9+np.linspace(10, 30, 21)*1e-9 for coupler in self.couplers
            # },
            # 'reset_pulse_amplitudes': {
            #     coupler: np.linspace(0.094, 0.1, 41) for coupler in self.couplers
            # },
            # cr g, f0 sweep
            # 'reset_pulse_durations': { # g
            #     qubit: np.linspace(0.075,0.175, 41)for qubit in self.coupled_qubits
            # },
            # 'reset_pulse_amplitudes': { # f0
            #     qubit: np.linspace(1.2, 1.7, 21) for qubit in self.coupled_qubits
            # },
            # cr ft, t sweep
            # 'reset_pulse_durations': {
            #     qubit: 2e-9+np.linspace(0, 60, 21)*1e-9 for qubit in self.coupled_qubits
            # },
            # 'reset_pulse_amplitudes': {
            #     qubit: np.linspace(0, 2, 21) for qubit in self.coupled_qubits
            # },
            # cr square sweep
            # 'reset_pulse_durations': {
            #     qubit: 2e-9+np.linspace(0, 100, 21)*1e-9 for qubit in self.coupled_qubits
            # },
            # 'reset_pulse_amplitudes': {
            #     qubit: np.linspace(0, 0.2, 41) for qubit in self.coupled_qubits
            # },
            # cr ramp sweep
            # 'reset_pulse_durations': {
            #     qubit: 2e-9+np.linspace(0, 40, 21)*1e-9 for qubit in self.coupled_qubits
            # },
            # 'reset_pulse_amplitudes': {
            #     qubit: np.linspace(0.2, 0.4, 41) for qubit in self.coupled_qubits
            # },
            # qc sweep g,ft
            # q23_q24
            # e
            # 'reset_pulse_durations': { # g
            #     qubit: np.linspace(0.01,0.5, 21)for qubit in self.coupled_qubits
            # },
            # 'reset_pulse_amplitudes': { # ft
            #     qubit: np.linspace(-0.01, -0.5, 21) for qubit in self.coupled_qubits
            # },
            # f
            # 'reset_pulse_durations': { # g
            #     qubit: np.linspace(0.05,0.1, 4)for qubit in self.coupled_qubits
            # },
            # 'reset_pulse_amplitudes': { # ft
            #     qubit: np.linspace(-0.2, -0.3, 4) for qubit in self.coupled_qubits
            # },
            # q22_q23
            # 'reset_pulse_durations': { # g
            #     qubit: np.linspace(0.001,0.1, 26)for qubit in self.coupled_qubits
            # },
            # 'reset_pulse_amplitudes': { # ft
            #     qubit: np.linspace(0, -0.4, 26) for qubit in self.coupled_qubits
            # },
            #  # f
            # 'reset_pulse_durations': { # g
            #     qubit: np.linspace(0.05,0.1, 4)for qubit in self.coupled_qubits
            # },
            # 'reset_pulse_amplitudes': { # ft
            #     qubit: np.linspace(-0.175, -0.275, 4) for qubit in self.coupled_qubits
            # }
            # qc sweep f0,t
            # q23_q24
            # 'reset_pulse_durations': {
            #     qubit: self.node_dictionary['duration_offset']*1e-9+np.linspace(0, 4, 5)*1e-9 for qubit in self.coupled_qubits
            # },
            # 'reset_pulse_amplitudes': {
            #     qubit: np.linspace(0.8, 1.1, 21) for qubit in self.coupled_qubits
            # },
            # f
            # 'reset_pulse_durations': {
            #     qubit: self.node_dictionary['duration_offset']*1e-9+np.linspace(0, 4, 5)*1e-9 for qubit in self.coupled_qubits
            # },
            # 'reset_pulse_amplitudes': {
            #     qubit: np.linspace(0.9, 1.15, 31) for qubit in self.coupled_qubits
            # },
            # q22_q23
            # 'reset_pulse_durations': {
            #     qubit: self.node_dictionary['duration_offset']*1e-9+np.linspace(0, 4, 5)*1e-9 for qubit in self.coupled_qubits
            # },
            # 'reset_pulse_amplitudes': {
            #     qubit: np.linspace(0.5, 0.8, 21) for qubit in self.coupled_qubits
            # },
            # f
            # 'reset_pulse_durations': {
            #     qubit: self.node_dictionary['duration_offset']*1e-9+np.linspace(0, 4, 5)*1e-9 for qubit in self.coupled_qubits
            # },
            # 'reset_pulse_amplitudes': {
            #     qubit: np.linspace(0.725, 0.825, 31) for qubit in self.coupled_qubits
            # },
            # For AC reset
            # 'reset_pulse_durations': {
            #     qubit: 4e-9+np.arange(0e-9, 36*100e-9,400e-9) for qubit in self.coupled_qubits
            # },
            # 'cz_pulse_frequencies_sweep': {
            #     qubit: np.linspace(210e6, 500e6, 51) + self.ac_freq for qubit in self.coupled_qubits
            # },
        }

        self.validate()

    def validate(self) -> None:
        all_coupled_qubits = []
        for coupler in self.couplers:
            all_coupled_qubits += coupler.split("_")
        if len(all_coupled_qubits) > len(set(all_coupled_qubits)):
            print("Couplers share qubits")
            raise ValueError("Improper Couplers")
