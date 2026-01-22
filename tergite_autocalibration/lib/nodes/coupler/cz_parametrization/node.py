# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024, 2025
# (C) Copyright Liangyu Chen 2023, 2024
# (C) Copyright Amr Osman, 2024
# (C) Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np
import xarray as xr

from tergite_autocalibration.config.globals import REDIS_CONNECTION
from tergite_autocalibration.lib.base.node import CouplerNode
from tergite_autocalibration.lib.nodes.coupler.cz_parametrization.analysis import (
    CZParametrizationNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.cz_parametrization.measurement import (
    CZParametrizationMeasurement,
)
from tergite_autocalibration.lib.nodes.external_parameter_node import (
    ExternalParameterNode,
)

PHASE_PATH = "via_20"


class CZParametrizationNode(CouplerNode):
    measurement_obj = CZParametrizationMeasurement
    analysis_obj = CZParametrizationNodeAnalysis
    measurement_type = ExternalParameterNode
    coupler_qois = ["cz_pulse_frequency", "cz_pulse_amplitude", "parking_current"]

    def __init__(self, name: str, all_qubits: list[str], couplers: list[str]):
        super().__init__(name, couplers)
        self.couplers = couplers

        self.coupled_qubits = self.get_coupled_qubits()
        self.all_qubits = self.coupled_qubits
        self.validate()

        self.schedule_keywords["loop_repetitions"] = 512 // 4
        self.schedule_keywords["cz_duration"] = 156e-9
        self.analysis_keywords["phase_path"] = PHASE_PATH
        self.loops = self.schedule_keywords["loop_repetitions"]
        self.ramp_back_to_zero = False

        self.external_samplespace = {
            "dc_currents": {
                coupler: self.broad_samplespace_around(self.parking_current(coupler))
                for coupler in self.couplers
            },
        }
        self.schedule_samplespace = {
            "cz_pulse_amplitudes": {
                coupler: np.linspace(0.15, 0.35, 30) for coupler in self.couplers
            },
            "cz_pulse_frequencies": {
                coupler: np.linspace(-7e6, 5e6, 20)
                + self.transition_frequency(coupler, phase_path=PHASE_PATH)
                for coupler in self.couplers
            },
        }

    def fine_samplespace_around(self, central_value: float) -> np.ndarray:
        return np.arange(central_value - 5e-6, central_value + 4.5e-6, 1e-6)

    def broad_samplespace_around(self, central_value: float) -> np.ndarray:
        return np.arange(central_value - 50e-6, central_value + 45e-6, 8e-6)

    def parking_current(self, coupler: str):
        return float(REDIS_CONNECTION.hget(f"couplers:{coupler}", "parking_current"))

    def initial_operation(self):
        pass

    def pre_measurement_operation(self, reduced_ext_space):
        iteration_dict = reduced_ext_space["dc_currents"]
        # there is some redundancy tha all qubits have the same
        # iteration index, that's why we keep the first value->
        this_iteration_value = list(iteration_dict.values())[0]
        dac_values = {}
        for coupler in self.couplers:
            this_iteration_value = iteration_dict[coupler]
            dac_values[coupler] = this_iteration_value
        self.spi_manager.set_dac_current(dac_values)

    def final_operation(self):
        """
        bring the current back to zero
        """
        if self.ramp_back_to_zero:
            dac_values = {}
            for coupler in self.couplers:
                dac_values[coupler] = 0
            self.spi_manager.set_dac_current(dac_values)

    def generate_dummy_dataset(self):
        dataset = xr.Dataset()
        for index, coupler in enumerate(self.couplers):
            number_of_amplitudes = len(
                self.schedule_samplespace["cz_pulse_amplitudes"][coupler]
            )
            number_of_frequencies = len(
                self.schedule_samplespace["cz_pulse_frequencies"][coupler]
            )
            number_of_iq_samples = (
                number_of_amplitudes * number_of_frequencies * self.loops
            )
            real_part = np.random.uniform(-1, 1, number_of_iq_samples)
            imag_part = np.random.uniform(-1, 1, number_of_iq_samples)
            complex_points = real_part + 1j * imag_part
            data_array = xr.DataArray(complex_points)

            dataset[2 * index] = data_array
            dataset[2 * index + 1] = data_array
        return dataset
