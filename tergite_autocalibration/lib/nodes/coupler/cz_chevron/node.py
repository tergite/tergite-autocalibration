# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024, 2025, 2026
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Amr Osman, 2024
# (C) Chalmers Next Labs 2025, 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from typing import Literal

import numpy as np
import xarray as xr

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.lib.base.node import CouplerNode
from tergite_autocalibration.lib.nodes.coupler.cz_chevron.analysis import (
    CZChevronAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_chevron.measurement import (
    CZChevronMeasurement,
)
from tergite_autocalibration.lib.nodes.schedule_node import OuterScheduleNode


class CZChevronNode(CouplerNode):
    name: str = "cz_chevron"
    measurement_obj = CZChevronMeasurement
    analysis_obj = CZChevronAnalysis
    measurement_type = OuterScheduleNode
    coupler_qois = ["cz_working_frequencies", "cz_working_durations_in_ns"]

    def __init__(self, couplers: list[str], **schedule_keywords):
        super().__init__(couplers, **schedule_keywords)

        self.couplers = couplers

        self.coupled_qubits = self.get_coupled_qubits()
        self.all_qubits = self.coupled_qubits
        self.validate()

        self.schedule_keywords["loop_repetitions"] = 512 // 4
        self.loops = self.schedule_keywords["loop_repetitions"]
        phase_paths = self.all_phase_paths()
        self.analysis_keywords = {
            coupler: {
                "phase_path": phase_paths[coupler],
                "number_of_working_points": 11,
            }
            for coupler in self.couplers
        }

        self.outer_schedule_samplespace = {
            "cz_pulse_frequencies": {
                coupler: np.linspace(-2.5e6, 1.5e6, 25)
                + self.known_cz_frequency(coupler)
                for coupler in self.couplers
            }
        }

        self.schedule_samplespace = {
            "cz_pulse_durations": {
                coupler: np.arange(24e-9, 240e-9, 8e-9) for coupler in self.couplers
            },
        }

    def known_cz_frequency(self, coupler: str):
        known_cz_frequency = float(
            REDIS_CONNECTION.hget(f"couplers:{coupler}", "cz_pulse_frequency")
        )
        return known_cz_frequency

    def all_phase_paths(self) -> dict[str, Literal["via_02", "via_20"]]:
        phase_paths = {}
        for coupler in self.couplers:
            path = REDIS_CONNECTION.hget(f"couplers:{coupler}", "cz_phase_path")
            phase_paths[coupler] = path
        return phase_paths

    def initial_operation(self):
        self.spi_manager.set_parking_currents(self.couplers)

    def generate_dummy_dataset(self):
        dataset = xr.Dataset()
        for index, coupler in enumerate(self.couplers):
            number_of_durations = len(
                self.schedule_samplespace["cz_pulse_durations"][coupler]
            )
            number_of_iq_samples = number_of_durations * self.loops
            real_part = np.random.uniform(-1, 1, number_of_iq_samples)
            imag_part = np.random.uniform(-1, 1, number_of_iq_samples)
            complex_points = real_part + 1j * imag_part
            data_array = xr.DataArray(complex_points)

            dataset[2 * index] = data_array
            dataset[2 * index + 1] = data_array
        return dataset
