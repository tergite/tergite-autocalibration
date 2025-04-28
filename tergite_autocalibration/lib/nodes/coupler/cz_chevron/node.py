# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Copyright Liangyu Chen 2024
# (C) Copyright Amr Osman 2024
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

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.utils.logging import logger
from tergite_autocalibration.lib.base.node import QubitNode
from tergite_autocalibration.lib.nodes.coupler.cz_chevron.analysis import (
    CZChevronAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_chevron.measurement import CZChevron


class CZChevronNode(QubitNode):
    measurement_obj = CZChevron
    analysis_obj = CZChevronAnalysis
    coupler_qois = ["cz_pulse_frequency", "cz_pulse_duration"]

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **node_dictionary
    ):
        super().__init__(name, all_qubits, **node_dictionary)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.qubit_state = 0
        self.all_qubits = [q for bus in couplers for q in bus.split("_")]
        self.coupler_samplespace = self.samplespace
        try:
            logger.info(f'{self.node_dictionary["cz_pulse_amplitude"] = }')
        except:
            amplitude = float(
                REDIS_CONNECTION.hget(f"couplers:{self.coupler}", "cz_pulse_amplitude")
            )
            logger.info(f"Amplitude found for coupler {self.coupler} : {amplitude}")
            if np.isnan(amplitude):
                amplitude = 0.375
                logger.info(
                    f"No amplitude found for coupler {self.coupler}. Using default value: {amplitude}"
                )
            self.node_dictionary["cz_pulse_amplitude"] = amplitude

        self.schedule_samplespace = {
            "cz_pulse_durations": {
                coupler: np.arange(0e-9, 401e-9, 20e-9) + 100e-9
                for coupler in self.couplers
            },
            "cz_pulse_frequencies": {
                coupler: np.linspace(-15e6, 10e6, 26)
                + self.transition_frequency(coupler)
                for coupler in self.couplers
            },
        }

        self.validate()

    def validate(self) -> None:
        all_coupled_qubits = []
        for coupler in self.couplers:
            all_coupled_qubits += coupler.split("_")
        if len(all_coupled_qubits) > len(set(all_coupled_qubits)):
            logger.info("Couplers share qubits")
            raise ValueError("Improper Couplers")

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
        # lo = 4.4e9 - (ac_freq - 450e6)
        # logger.info(f'{ ac_freq/1e6 = } MHz for coupler: {coupler}')
        # logger.info(f'{ lo/1e9 = } GHz for coupler: {coupler}')
        return ac_freq


class CZOptimizeChevronNode(QubitNode):
    measurement_obj = CZChevron
    analysis_obj = CZChevronAnalysis
    coupler_qois = ["cz_pulse_frequency", "cz_pulse_duration"]

    def __init__(self, name: str, all_qubits: list[str], couplers: list[str]):
        super().__init__(name, all_qubits)
        self.type = "optimized_sweep"
        self.couplers = couplers
        self.coupler = self.couplers[0]
        self.optimization_field = "cz_pulse_duration"
        self.qubit_state = 0
        self.all_qubits = [q for bus in couplers for q in bus.split("_")]
        self.schedule_samplespace = {
            "cz_pulse_durations": {
                coupler: np.arange(100e-9, 1000e-9, 320e-9) for coupler in self.couplers
            },
            "cz_pulse_frequencies": {
                coupler: np.linspace(-2.0e6, 2.0e6, 5)
                + self.transition_frequency(coupler)
                for coupler in self.couplers
            },
        }
        self.coupler_samplespace = self.schedule_samplespace
        self.validate()

    def validate(self) -> None:
        all_coupled_qubits = []
        for coupler in self.couplers:
            all_coupled_qubits += coupler.split("_")
        if len(all_coupled_qubits) > len(set(all_coupled_qubits)):
            logger.info("Couplers share qubits")
            raise ValueError("Improper Couplers")

    def transition_frequency(self, coupler: str):
        coupled_qubits = coupler.split(sep="_")
        q1_f01 = float(
            REDIS_CONNECTION.hget(f"transmons:{coupled_qubits[0]}", "freq_01")
        )
        q2_f01 = float(
            REDIS_CONNECTION.hget(f"transmons:{coupled_qubits[1]}", "freq_01")
        )
        q1_f12 = float(
            REDIS_CONNECTION.hget(f"transmons:{coupled_qubits[0]}", "freq_12")
        )
        q2_f12 = float(
            REDIS_CONNECTION.hget(f"transmons:{coupled_qubits[1]}", "freq_12")
        )
        # ac_freq = np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12))
        ac_freq = np.max(
            [
                np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12)),
                np.abs(q1_f01 + q2_f01 - (q2_f01 + q2_f12)),
            ]
        )
        ac_freq = int(ac_freq / 1e4) * 1e4
        logger.info(f"{ ac_freq/1e6 = } MHz for coupler: {coupler}")
        return ac_freq


class CZChevronSweepNode(QubitNode):
    measurement_obj = CZChevron
    analysis_obj = CZChevronAnalysis
    coupler_qois = ["cz_pulse_frequency", "cz_pulse_duration"]

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.all_qubits = all_qubits
        self.couplers = couplers
        self.edges = couplers
        self.coupler = self.couplers[0]
        self.qubit_state = 0
        self.all_qubits = [q for bus in couplers for q in bus.split("_")]

        self.schedule_samplespace = {
            "cz_pulse_amplitudes": {
                coupler: np.linspace(0.2, 0.4, 10) for coupler in self.couplers
            },
            "cz_pulse_frequencies": {
                coupler: np.linspace(-15e6, 10e6, 26)
                + self.transition_frequency(coupler)
                for coupler in self.couplers
            },
        }

        self.validate()

    def validate(self) -> None:
        all_coupled_qubits = []
        for coupler in self.couplers:
            all_coupled_qubits += coupler.split("_")
        if len(all_coupled_qubits) > len(set(all_coupled_qubits)):
            logger.info("Couplers share qubits")
            raise ValueError("Improper Couplers")

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
        return ac_freq
