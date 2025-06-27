# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
# (C) Copyright Michele Faucci Giannelli 2024, 2025
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
    ResonatorSpectroscopyVsCurrentNodeAnalysis,
    QubitSpectroscopyVsCurrentNodeAnalysis,
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
from tergite_autocalibration.utils.logging import logger


class QubitSpectroscopyVsCurrentNode(ExternalParameterFixedScheduleCouplerNode):
    """
    This node performs a qubit spectroscopy measurement while varying the
    current through the coupler to measure the crossing point of the coupler with the qubit.
    """

    measurement_obj = TwoTonesMultidimMeasurement
    analysis_obj = QubitSpectroscopyVsCurrentNodeAnalysis
    # coupler_qois = ["parking_current"]
    coupler_qois = ["qubit_crossing_points"]

    def __init__(self, name: str, couplers: list[str], **schedule_keywords):
        super().__init__(name, couplers, **schedule_keywords)
        self.qubit_state = 0
        self.dacs = []
        self.schedule_keywords["qubit_state"] = self.qubit_state

        self.schedule_samplespace = {
            "spec_frequencies": {
                qubit: qubit_samples(qubit) for qubit in self.all_qubits
            }
        }

        self.external_samplespace = {
            "dc_currents": {
                coupler: np.arange(-2.5e-3, 2.5e-3, 50e-6) for coupler in self.couplers
            },
        }
        self.validate()

    def pre_measurement_operation(self, reduced_ext_space):
        self.spi_manager.set_dac_current(reduced_ext_space["dc_currents"])

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
        currents = {}
        for coupler in self.couplers:
            currents[coupler] = 0

        self.spi_manager.set_dac_current(currents)


class ResonatorSpectroscopyVsCurrentNode(ExternalParameterFixedScheduleCouplerNode):
    """
    This node performs a resonator spectroscopy measurement while varying the
    current through the coupler to measure the crossing point of the coupler with the resonator.
    """

    measurement_obj = ResonatorSpectroscopyMeasurement
    analysis_obj = ResonatorSpectroscopyVsCurrentNodeAnalysis
    # coupler_qois = ["resonator_flux_quantum"]
    coupler_qois = ["resonator_crossing_points"]

    def __init__(self, name: str, couplers: list[str], **schedule_keywords):
        super().__init__(name, couplers, **schedule_keywords)
        self.qubit_state = 0
        self.dacs = []

        self.schedule_samplespace = {
            "ro_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            }
        }

        self.external_samplespace = {
            "dc_currents": {
                coupler: np.arange(-1e-3, 1e-3, 50e-6) for coupler in self.couplers
            },
        }
        self.validate()

    def pre_measurement_operation(self, reduced_ext_space):
        self.spi_manager.set_dac_current(reduced_ext_space["dc_currents"])

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
        currents = {}
        for coupler in self.couplers:
            currents[coupler] = 0

        self.spi_manager.set_dac_current(currents)
        