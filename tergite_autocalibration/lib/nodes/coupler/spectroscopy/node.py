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
import xarray
from lmfit.models import LorentzianModel

from tergite_autocalibration.config.globals import CONFIG
from tergite_autocalibration.lib.base.node import CouplerNode
from tergite_autocalibration.lib.nodes.coupler.spectroscopy.analysis import (
    CouplerSpectroscopyNodeAnalysis,
)
from tergite_autocalibration.lib.nodes.coupler.spectroscopy.measurement import (
    CouplerSpectroscopyMeasurement,
)
from tergite_autocalibration.lib.nodes.external_parameter_node import (
    ExternalParameterNode,
)
from tergite_autocalibration.lib.utils.samplespace import (
    qubit_samples,
    resonator_samples,
)
from tergite_autocalibration.utils.logging import logger

peak = LorentzianModel()


class CouplerDCSpectroscopyNode(CouplerNode):
    """
    This node performs a qubit spectroscopy measurement while varying the
    current through the coupler to measure the crossing point of the coupler with the qubit.
    """

    name: str = "coupler_dc_spectroscopy"
    measurement_obj = CouplerSpectroscopyMeasurement
    analysis_obj = CouplerSpectroscopyNodeAnalysis
    measurement_type = ExternalParameterNode
    coupler_qois = ["fmax", "Ic", "I0", "offset"]

    def __init__(self, couplers: list[str], **schedule_keywords):
        super().__init__(couplers, **schedule_keywords)

        self.samplespace_structure = "parallel"

        self.schedule_samplespace = {
            "qubit_frequencies": {
                qubit: qubit_samples(qubit) for qubit in self.all_qubits
            },
            "resonator_frequencies": {
                qubit: resonator_samples(qubit) for qubit in self.all_qubits
            },
        }

        self.external_samplespace = {
            "dc_currents": {
                coupler: np.arange(-2e-3, 2e-3, 80e-6) for coupler in self.couplers
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
            qubit_freq = CONFIG.device.qubits[qubit]["VNA_f01_frequency"]
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
            qu_samples = qubit_samples(qubit)
            ro_samples = resonator_samples(qubit)
            number_of_qu_samples = len(qu_samples)
            number_of_ro_samples = len(ro_samples)
            number_of_samples = number_of_qu_samples + number_of_ro_samples
            qu_frequencies = np.linspace(
                qu_samples[0], qu_samples[-1], number_of_qu_samples
            )
            ro_frequencies = np.linspace(
                ro_samples[0], ro_samples[-1], number_of_ro_samples
            )
            true_s21_qu = peak.eval(params=true_params, x=qu_frequencies)
            true_s21_ro = peak.eval(params=true_params, x=ro_frequencies)
            true_s21 = np.concatenate((true_s21_qu, true_s21_ro))
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
