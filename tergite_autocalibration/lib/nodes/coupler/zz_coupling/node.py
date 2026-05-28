# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2026
# (C) Chalmers Next Labs 2026
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

from tergite_autocalibration.lib.base.node import CouplerNode
from tergite_autocalibration.lib.nodes.coupler.zz_coupling.analysis import (
    ZZCouplingNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.zz_coupling.measurement import (
    ZZCouplingMeasurement,
)
from tergite_autocalibration.lib.nodes.schedule_node import ScheduleNode
from tergite_autocalibration.lib.utils.analysis_models import RamseyModel

ramsey_model = RamseyModel()


class ZZCouplingNode(CouplerNode):
    name: str = "zz_coupling"
    measurement_obj = ZZCouplingMeasurement
    analysis_obj = ZZCouplingNodeAnalysis
    measurement_type = ScheduleNode
    coupler_qois = ["zz_coupling"]

    def __init__(self, couplers: list[str], **schedule_keywords):
        super().__init__(couplers, **schedule_keywords)

        self.couplers = couplers

        self.coupled_qubits = self.get_coupled_qubits()
        self.all_qubits = self.coupled_qubits
        self.validate()

        self.schedule_keywords["coupler_dict"] = self.qubit_types()
        self.analysis_keywords = self.qubit_types()

        self.schedule_samplespace = {
            "ramsey_delays": {
                qubit: np.arange(4e-9, 2048e-9, 12 * 8e-9) for qubit in self.all_qubits
            },
            "artificial_detunings": {
                qubit: np.arange(-2.1, 2.1, 0.8) * 1e6 for qubit in self.all_qubits
            },
            "spectator_states": {
                coupler: np.array([0, 1], dtype=np.int8) for coupler in self.couplers
            },
        }

    def qubit_types(self) -> dict[str, dict]:
        qubit_types_dict = {}
        for coupler in self.couplers:
            # NOTE: as is, the convention is that the first qubit is active
            # and the second is spectator
            active_qubit, spectator_qubit = coupler.split("_")
            qubit_types_dict[coupler] = {
                "active_qubit": active_qubit,
                "spectator_qubit": spectator_qubit,
            }
        return qubit_types_dict

    def initial_operation(self):
        self.spi_manager.set_initial_parking_currents(self.couplers)

    def generate_dummy_dataset(self, noise=False):
        dataset = xr.Dataset()
        real_detuning = 200e3
        noise_scale = 0.02
        first_qubit = self.all_qubits[0]
        first_coupler = self.couplers[0]
        detunings = self.schedule_samplespace["artificial_detunings"][first_qubit]
        spectator_states = self.schedule_samplespace["spectator_states"][first_coupler]
        samples = self.schedule_samplespace["ramsey_delays"][first_qubit]
        number_of_samples = len(samples)
        delays = np.linspace(samples[0], samples[-1], number_of_samples)
        for index, _ in enumerate(self.all_qubits):
            data_array = np.array([])
            for spectator_state in spectator_states:
                for detuning in detunings:
                    measured_detuning = np.abs(detuning - real_detuning)
                    true_params = ramsey_model.make_params(
                        amplitude=0.2,
                        frequency=measured_detuning,
                        tau=80e-6,
                        phase=0,
                        offset=0,
                    )
                    np.random.seed(123)
                    true_s21 = ramsey_model.eval(params=true_params, t=delays)

                    noise_s21 = noise_scale * (
                        np.random.randn(number_of_samples)
                        + 1j * np.random.randn(number_of_samples)
                    )
                    measured_s21 = true_s21
                    if noise:
                        measured_s21 += noise_s21
                    data_array = np.concatenate((data_array, measured_s21))

            # Add the DataArray to the Dataset with an integer name (converted to string)
            dataset[index] = xr.DataArray(data_array)
        return dataset
