# This code is part of Tergite
#
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np

from .....config.settings import REDIS_CONNECTION
from .analysis import (
    CZParametrisationFixDurationNodeAnalysis,
)
from .measurement import (
    CZParametrisationFixDuration,
)
from ....utils.node_subclasses import ParametrizedSweepNode


class CZParametrisationFixDurationNode(ParametrizedSweepNode):
    measurement_obj = CZParametrisationFixDuration
    analysis_obj = CZParametrisationFixDurationNodeAnalysis

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        self.all_qubits = all_qubits  # [q for bus in couplers for q in bus.split("_")]
        super().__init__(name, self.all_qubits, **schedule_keywords)
        self.type = "parameterized_sweep"
        self.couplers = couplers
        self.edges = couplers
        print(couplers)
        self.coupler = couplers[0]
        self.schedule_keywords = schedule_keywords
        self.backup = False

        self.redis_field = [
            "cz_pulse_frequency",
            "cz_pulse_amplitude",
            "cz_parking_current",
        ]
        self.node_dictionary[
            "cz_pulse_duration"
        ] = 120e-9  # Need to make it configurable

        # Should these sample space move to user defined inputs?
        self.initial_schedule_samplespace = {
            "cz_pulse_amplitudes": {
                coupler: np.linspace(0.01, 0.35, 15) for coupler in self.couplers
            },
            "cz_pulse_frequencies": {
                coupler: np.linspace(-20e6, 20e6, 21)
                + self.transition_frequency(coupler)
                for coupler in self.couplers
            },
        }
        self.external_samplespace = {
            "cz_parking_currents": {
                coupler: np.array([-0.640, -0.650, -0.660, -0.670, -0.680])
                for coupler in self.couplers
            }
            # np.arange(-0.3, 0.3, 10) * self.coupler_current_range + self.coupler_current for coupler in self.couplers
        }

        self.validate()

    def validate(self) -> None:
        all_coupled_qubits = []
        for coupler in self.couplers:
            all_coupled_qubits += coupler.split("_")
        if len(all_coupled_qubits) > len(set(all_coupled_qubits)):
            raise ValueError("Couplers with two identical qubits")
        if not all(element in self.all_qubits for element in all_coupled_qubits):
            raise ValueError("Cloupler qubits not in all qubits")

    def transition_frequency(self, coupler: str):
        coupled_qubits = coupler.split(sep="_")
        q1_f01 = float(
            REDIS_CONNECTION.hget(f"transmons:{coupled_qubits[0]}", "clock_freqs:f01")
        )
        q2_f01 = float(
            REDIS_CONNECTION.hget(f"transmons:{coupled_qubits[1]}", "clock_freqs:f01")
        )
        q1_f12 = float(
            REDIS_CONNECTION.hget(f"transmons:{coupled_qubits[0]}", "clock_freqs:f12")
        )
        q2_f12 = float(
            REDIS_CONNECTION.hget(f"transmons:{coupled_qubits[1]}", "clock_freqs:f12")
        )
        # ac_freq = np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12))
        ac_freq = np.max(
            [
                np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12)),
                np.abs(q1_f01 + q2_f01 - (q2_f01 + q2_f12)),
            ]
        )
        ac_freq = int(ac_freq / 1e4) * 1e4
        print(f"{ ac_freq/1e6 = } MHz for coupler: {coupler}")
        return ac_freq

    def coupler_current(self):
        current = float(
            REDIS_CONNECTION.hget(f"couplers:{self.couplers[0]}", "parking_current")
        )
        return current

    def coupler_current_range(self):
        current_range = float(
            REDIS_CONNECTION.hget(f"couplers:{self.couplers[0]}", "current_range")
        )
        return current_range

    def pre_measurement_operation(self, reduced_ext_space: dict):
        self.schedule_samplespace = (
            self.initial_schedule_samplespace | reduced_ext_space
        )
