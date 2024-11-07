# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
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

from tergite_autocalibration.lib.base.node import BaseNode
from tergite_autocalibration.lib.nodes.coupler.spectroscopy.analysis import CouplerSpectroscopyNodeAnalysis
from tergite_autocalibration.lib.nodes.qubit_control.spectroscopy.measurement import Two_Tones_Multidim
from tergite_autocalibration.lib.nodes.readout.resonator_spectroscopy.measurement import Resonator_Spectroscopy
from tergite_autocalibration.utils.dto.enums import MeasurementMode
from tergite_autocalibration.utils.hardware_utils import SpiDAC
from tergite_autocalibration.utils.user_input import qubit_samples, resonator_samples


class Coupler_Spectroscopy_Node(BaseNode):
    measurement_obj = Two_Tones_Multidim
    analysis_obj = CouplerSpectroscopyNodeAnalysis
    coupler_qois = ["parking_current", "current_range"]

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.name = name
        self.all_qubits = all_qubits  # this is a Base attr, delete it here
        self.couplers = couplers
        self.qubit_state = 0
        self.type = "spi_and_cluster_simple_sweep"
        # perform 2 tones while biasing the current
        self.coupled_qubits = self.get_coupled_qubits()
        self.coupler = self.couplers[0]

        # This should go in node or in measurement
        # self.mode = MeasurementMode.real
        # self.spi_dac = SpiDAC(self.mode)
        # self.dac = self.spi_dac.create_spi_dac(self.coupler)

        self.all_qubits = self.coupled_qubits

        self.schedule_samplespace = {
            "spec_frequencies": {
                qubit: qubit_samples(qubit) for qubit in self.all_qubits
            }
        }

        self.external_samplespace = {
            "dc_currents": {self.coupler: np.arange(-2.5e-3, 2.5e-3, 150e-6)},
        }
        # self.validate()

    def get_coupled_qubits(self) -> list:
        if len(self.couplers) > 1:
            print("Multiple couplers, lets work with only one")
        coupled_qubits = self.couplers[0].split(sep="_")
        self.coupler = self.couplers[0]
        return coupled_qubits

    def pre_measurement_operation(self, reduced_ext_space):
        iteration_dict = reduced_ext_space["dc_currents"]
        # there is some redundancy tha all qubits have the same
        # iteration index, that's why we keep the first value->

        this_iteration_value = list(iteration_dict.values())[0]
        print(f"{ this_iteration_value = }")
        self.spi_dac.set_dac_current(self.dac, this_iteration_value)


class Coupler_Resonator_Spectroscopy_Node(BaseNode):
    measurement_obj = Resonator_Spectroscopy
    analysis_obj = CouplerSpectroscopyNodeAnalysis
    coupler_qois = ["resonator_flux_quantum"]

    def __init__(
        self, name: str, all_qubits: list[str], couplers: list[str], **schedule_keywords
    ):
        super().__init__(name, all_qubits, **schedule_keywords)
        self.qubit_state = 0
        self.couplers = couplers
        self.coupler = self.couplers[0]
        mode = MeasurementMode.real
        self.spi_dac = SpiDAC(mode)
        self.dac = self.spi_dac.create_spi_dac(self.coupler)
        self.coupled_qubits = self.get_coupled_qubits()

        self.all_qubits = self.coupled_qubits

        self.schedule_samplespace = {
            "ro_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }

        self.external_samplespace = {
            "dc_currents": {self.coupler: np.arange(-2.5e-3, 2.5e-3, 500e-6)},
        }

    def get_coupled_qubits(self) -> list:
        if len(self.couplers) > 1:
            print("Multiple couplers, lets work with only one")
        coupled_qubits = self.couplers[0].split(sep="_")
        self.coupler = self.couplers[0]
        return coupled_qubits

    def pre_measurement_operation(self, reduced_ext_space):
        iteration_dict = reduced_ext_space["dc_currents"]
        # there is some redundancy tha all qubits have the same
        # iteration index, that's why we keep the first value->

        this_iteration_value = list(iteration_dict.values())[0]
        print(f"{ this_iteration_value = }")
        self.spi_dac.set_dac_current(self.dac, this_iteration_value)
