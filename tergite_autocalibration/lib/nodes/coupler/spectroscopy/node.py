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

from pathlib import Path
import numpy as np
from quantify_scheduler import CompiledSchedule
import quantify_scheduler.backends.qblox.constants as constants
from quantify_scheduler.backends import SerialCompiler

from tergite_autocalibration.lib.nodes.coupler.spectroscopy.analysis import (
    CouplerSpectroscopyNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.external_parameter_node import (
    ExternalParameterFixedScheduleCouplerNode,
)
from tergite_autocalibration.lib.nodes.qubit_control.spectroscopy.measurement import (
    TwoTonesMultidimMeasurement,
)
from tergite_autocalibration.lib.nodes.readout.resonator_spectroscopy.measurement import (
    ResonatorSpectroscopyMeasurement,
)
from tergite_autocalibration.lib.utils.samplespace import (
    qubit_samples,
    resonator_samples,
)
from tergite_autocalibration.utils.dto.enums import MeasurementMode
from tergite_autocalibration.utils.hardware.spi import SpiDAC
from tergite_autocalibration.utils.logging import logger


class CouplerSpectroscopyNode(ExternalParameterFixedScheduleCouplerNode):
    measurement_obj = TwoTonesMultidimMeasurement
    analysis_obj = CouplerSpectroscopyNodeAnalysis
    coupler_qois = ["parking_current", "current_range"]

    def __init__(self, name: str, couplers: list[str], **schedule_keywords):
        super().__init__(name, couplers, **schedule_keywords)
        self.name = name
        self.couplers = couplers
        self.qubit_state = 0
        self.schedule_keywords["qubit_state"] = self.qubit_state
        self.coupled_qubits = self.get_coupled_qubits()
        self.coupler = self.couplers[0]

        # This should go in node or in measurement
        self.mode = MeasurementMode.real
        self.spi_dac = SpiDAC(self.mode)
        self.dac = self.spi_dac.create_spi_dac(self.coupler)

        self.all_qubits = self.coupled_qubits

        self.schedule_samplespace = {
            "spec_frequencies": {
                qubit: qubit_samples(qubit) for qubit in self.all_qubits
            }
        }

        self.external_samplespace = {
            "dc_currents": {self.coupler: np.arange(-2.5e-4, 2.5e-4, 280e-6)},
        }
        self.validate()

    def calibrate(self, data_path: Path, cluster_status):
        if cluster_status == MeasurementMode.real:
            self.spi_dac = SpiDAC(cluster_status)

        super().calibrate(data_path, cluster_status)

    def pre_measurement_operation(self, reduced_ext_space):
        iteration_dict = reduced_ext_space["dc_currents"]
        # there is some redundancy tha all qubits have the same
        # iteration index, that's why we keep the first value->

        this_iteration_value = list(iteration_dict.values())[0]
        logger.info(f"{ this_iteration_value = }")
        self.spi_dac.set_dac_current(self.dac, this_iteration_value)

    def precompile(self, schedule_samplespace: dict) -> CompiledSchedule:
        constants.GRID_TIME_TOLERANCE_TIME = 5e-2

        # TODO: put 'tof' out of its misery
        if self.name == "tof":
            return None, 1

        transmons = self.device_manager.transmons

        measurement_class = self.measurement_obj(transmons)
        schedule = measurement_class.schedule_function(
            **schedule_samplespace, **self.schedule_keywords
        )

        # TODO: Probably the compiler desn't need to be created every time self.precompile() is called.
        compiler = SerialCompiler(name=f"{self.name}_compiler")

        compilation_config = self.device.generate_compilation_config()
        logger.info("Starting Compiling")
        compiled_schedule = compiler.compile(
            schedule=schedule, config=compilation_config
        )

        return compiled_schedule

    def final_operation(self):
        logger.info("Final Operation")
        self.spi_dac.set_dac_current(self.dac, 0)


class CouplerResonatorSpectroscopyNode(ExternalParameterFixedScheduleCouplerNode):
    measurement_obj = ResonatorSpectroscopyMeasurement
    analysis_obj = CouplerSpectroscopyNodeAnalysis
    coupler_qois = ["resonator_flux_quantum"]

    def __init__(self, name: str, couplers: list[str], **schedule_keywords):
        super().__init__(name, couplers, **schedule_keywords)
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
        self.validate()

    def calibrate(self, data_path: Path, cluster_status):
        if cluster_status == MeasurementMode.real:
            self.spi_dac = SpiDAC(cluster_status)

        super().calibrate(data_path, cluster_status)

    def pre_measurement_operation(self, reduced_ext_space):
        iteration_dict = reduced_ext_space["dc_currents"]
        # there is some redundancy tha all qubits have the same
        # iteration index, that's why we keep the first value->

        this_iteration_value = list(iteration_dict.values())[0]
        logger.info(f"{ this_iteration_value = }")
        self.spi_dac.set_dac_current(self.dac, this_iteration_value)

    def precompile(self, schedule_samplespace: dict) -> CompiledSchedule:
        constants.GRID_TIME_TOLERANCE_TIME = 5e-2

        # TODO: put 'tof' out of its misery
        if self.name == "tof":
            return None, 1

        transmons = self.device_manager.transmons

        measurement_class = self.measurement_obj(transmons)
        schedule = measurement_class.schedule_function(
            **schedule_samplespace, **self.schedule_keywords
        )

        # TODO: Probably the compiler desn't need to be created every time self.precompile() is called.
        compiler = SerialCompiler(name=f"{self.name}_compiler")

        compilation_config = self.device.generate_compilation_config()
        logger.info("Starting Compiling")
        compiled_schedule = compiler.compile(
            schedule=schedule, config=compilation_config
        )

        return compiled_schedule

    def final_operation(self):
        logger.info("Final Operation")
        self.spi_dac.set_dac_current(self.dac, 0)
