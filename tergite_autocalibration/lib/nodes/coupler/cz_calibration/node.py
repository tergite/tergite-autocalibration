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

import ast

import numpy as np
import xarray as xr

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.lib.base.node import CouplerNode
from tergite_autocalibration.lib.nodes.coupler.cz_calibration.analysis import (
    CZCalibrationNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_calibration.measurement import (
    CZ_CalibrationMeasurement,
)
from tergite_autocalibration.lib.nodes.schedule_node import OuterScheduleNode


class CZ_CalibrationNode(CouplerNode):
    measurement_obj = CZ_CalibrationMeasurement
    analysis_obj = CZCalibrationNodeAnalysis
    measurement_type = OuterScheduleNode
    coupler_qois = ["cz_pulse_frequency", "cz_pulse_duration"]

    def __init__(self, name: str, couplers: list[str], **schedule_keywords):
        super().__init__(name, couplers, **schedule_keywords)
        self.couplers = couplers

        self.coupled_qubits = self.get_coupled_qubits()
        self.all_qubits = self.coupled_qubits

        self.schedule_keywords["loop_repetitions"] = 512
        self.loops = self.schedule_keywords["loop_repetitions"]

        self.schedule_keywords["coupler_dict"] = self.gate_qubit_types_dict()
        self.validate()

        self.outer_schedule_samplespace = {
            "working_points": {
                coupler: self.working_points(coupler) for coupler in self.couplers
            }
        }
        self.schedule_samplespace = {
            "ramsey_phases": {
                qubit: np.linspace(0, 420, 30) for qubit in self.coupled_qubits
            },
            "control_ons": {
                coupler: np.array([False, True]) for coupler in self.couplers
            },
        }

    def working_frequencies(self, coupler: str):
        frequency_list_string_representation = REDIS_CONNECTION.hget(
            f"couplers:{coupler}", "cz_working_frequencies"
        )
        frequency_list = ast.literal_eval(frequency_list_string_representation)
        return np.array(frequency_list)

    def working_durations_in_ns(self, coupler: str):
        duration_in_ns_string_representation = REDIS_CONNECTION.hget(
            f"couplers:{coupler}", "cz_working_durations_in_ns"
        )
        duration_in_ns_list = ast.literal_eval(duration_in_ns_string_representation)
        return np.array(duration_in_ns_list) * 1e-9

    def working_points(self, coupler: str):
        working_points = zip(
            self.working_frequencies(coupler), self.working_durations_in_ns(coupler)
        )
        working_points_array = np.array(list(working_points))
        return working_points_array

    def initial_operation(self):
        self.spi_manager.set_parking_currents(self.couplers)

    def generate_dummy_dataset(self):
        dataset = xr.Dataset()
        for index, coupler in enumerate(self.couplers):
            qubit_1, qubit_2 = coupler.split("_")
            number_of_phases = len(self.schedule_samplespace["ramsey_phases"][qubit_1])
            number_of_modes = len(self.schedule_samplespace["control_ons"][coupler])
            number_of_iq_samples = number_of_phases * number_of_modes * self.loops
            real_part = np.random.uniform(-1, 1, number_of_iq_samples)
            imag_part = np.random.uniform(-1, 1, number_of_iq_samples)
            complex_points = real_part + 1j * imag_part
            data_array = xr.DataArray(complex_points)

            dataset[2 * index] = data_array
            dataset[2 * index + 1] = data_array
        return dataset
