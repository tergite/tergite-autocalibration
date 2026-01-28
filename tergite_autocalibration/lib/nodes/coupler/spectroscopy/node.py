# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024, 2025
# (C) Copyright Michele Faucci Giannelli 2024, 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


import numpy as np
import quantify_scheduler.backends.qblox.constants as constants
import xarray
from lmfit.models import LorentzianModel
from quantify_scheduler import CompiledSchedule
from quantify_scheduler.backends import SerialCompiler

from tergite_autocalibration.config.legacy import dh
from tergite_autocalibration.lib.base.node import CouplerNode
from tergite_autocalibration.lib.nodes.coupler.spectroscopy.analysis import (
    CouplerAnticrossingNodeAnalysis,
    ResonatorSpectroscopyVsCurrentNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.external_parameter_node import (
    ExternalParameterNode,
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
from tergite_autocalibration.utils.logging import logger

peak = LorentzianModel()


class QubitSpectroscopyVsCurrentNode(CouplerNode):
    """
    This node performs a qubit spectroscopy measurement while varying the
    current through the coupler to measure the crossing point of the coupler with the qubit.
    """

    name: str = "qubit_spectroscopy_vs_current"
    measurement_obj = TwoTonesMultidimMeasurement
    analysis_obj = CouplerAnticrossingNodeAnalysis
    measurement_type = ExternalParameterNode
    coupler_qois = ["control_qubit_crossing_points", "target_qubit_crossing_points"]

    def __init__(self, couplers: list[str], **schedule_keywords):
        super().__init__(couplers, **schedule_keywords)
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
                coupler: np.arange(-1.5e-3, 1.5e-3, 100e-6) for coupler in self.couplers
            },
        }
        self.validate()

    def initial_operation(self):
        pass

    def pre_measurement_operation(self, reduced_ext_space):
        first_coupler = self.couplers[0]
        self.this_current = reduced_ext_space["dc_currents"][first_coupler]
        self.spi_manager.set_dac_current(reduced_ext_space["dc_currents"])

    def final_operation(self):
        logger.info("Final Operation")
        currents = {}
        for coupler in self.couplers:
            currents[coupler] = 0

        self.spi_manager.set_dac_current(currents)

    def generate_dummy_dataset(self):
        dataset = xarray.Dataset()
        for index, qubit in enumerate(self.all_qubits):
            qubit_freq = dh.get_legacy("VNA_qubit_frequencies")[qubit]
            epsilon = 3 / 5 * 1e-7  # to avoid divide by zero
            low_asymptote = -0.001 + epsilon
            high_asymptote = 0.001 + epsilon
            shifted_frequency = qubit_freq + 2e6 * np.abs(
                low_asymptote * high_asymptote
            ) / (self.this_current - low_asymptote) / (
                self.this_current - high_asymptote
            )
            true_params = peak.make_params(
                amplitude=0.2, center=shifted_frequency, sigma=0.1e6
            )
            samples = qubit_samples(qubit)
            number_of_samples = len(samples)
            frequncies = np.linspace(samples[0], samples[-1], number_of_samples)
            true_s21 = peak.eval(params=true_params, x=frequncies)
            noise_scale = 0.02

            np.random.seed(123)
            measured_s21 = true_s21 + 0 * noise_scale * (
                np.random.randn(number_of_samples)
                + 1j * np.random.randn(number_of_samples)
            )
            data_array = xarray.DataArray(measured_s21)

            # Add the DataArray to the Dataset with an integer name (converted to string)
            dataset[index] = data_array
        return dataset


class ResonatorSpectroscopyVsCurrentNode(CouplerNode):
    """
    This node performs a resonator spectroscopy measurement while varying the
    current through the coupler to measure the crossing point of the coupler with the resonator.
    """

    name: str = "resonator_spectroscopy_vs_current"
    measurement_obj = ResonatorSpectroscopyMeasurement
    analysis_obj = ResonatorSpectroscopyVsCurrentNodeAnalysis
    measurement_type = ExternalParameterNode
    # coupler_qois = ["resonator_flux_quantum"]
    coupler_qois = [
        "control_resonator_crossing_points",
        "target_resonator_crossing_points",
    ]

    def __init__(self, couplers: list[str], **schedule_keywords):
        super().__init__(couplers, **schedule_keywords)
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
